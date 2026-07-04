from __future__ import annotations

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.models.schemas import AskResponse, HistoryMessage
from app.services.search_service import SearchService

log = structlog.get_logger()

_SYSTEM_PROMPT = """\
You are a helpful assistant that answers questions strictly based on the provided context.

Rules:
- Answer only from the context below. Do not use outside knowledge.
- If the context does not contain enough information, say "I could not find a clear answer in the provided documents."
- Be concise and direct.
- Do not make up information.
- Do NOT mention source numbers, filenames, chunk references, or any internal labels in your answer. Just answer naturally.
"""


class AskService:
    def __init__(self, search_service: SearchService, llm: BaseChatModel, llm_name: str):
        self._search = search_service
        self._llm_name = llm_name

        # ChatPromptTemplate builds the message list declaratively.
        # MessagesPlaceholder("history") injects conversation turns as a block between
        # the system prompt and the current question — optional=True means it works
        # even when no history is passed (first message in a session).
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT + "\n\nContext:\n{context}"),
            MessagesPlaceholder("history", optional=True),
            ("human", "{question}"),
        ])

        # LCEL chain: prompt → llm → extract plain string.
        # The | pipe means output of left feeds input of right:
        #   prompt.invoke(inputs) → list of messages
        #   llm.invoke(messages)  → AIMessage object
        #   StrOutputParser()     → extracts .content → plain string
        #
        # Swap llm from ChatOllama to ChatOpenAI to ChatAnthropic — this chain
        # stays exactly the same because BaseChatModel is a universal interface.
        self._chain = prompt | llm | StrOutputParser()

    async def ask(
        self,
        tenant_slug: str,
        question: str,
        top_k: int = 5,
        min_score: float = 0.5,
        history: list[HistoryMessage] | None = None,
    ) -> AskResponse:
        # Step 1: retrieve relevant chunks above the confidence threshold
        search_resp = await self._search.search(tenant_slug, question, top_k, min_score)

        if not search_resp.results:
            return AskResponse(
                question=question,
                answer="I could not find any relevant content in the documents for this tenant.",
                sources=[],
                llm_provider=self._llm_name,
            )

        # Step 2: build context — no labels so the LLM has nothing to cite
        context = "\n\n".join(r.chunk_text for r in search_resp.results)

        # Step 3: convert our HistoryMessage list into LangChain typed message objects.
        # LangChain uses HumanMessage / AIMessage instead of raw dicts because different
        # providers format these differently internally — LangChain handles that translation.
        lc_history: list[HumanMessage | AIMessage] = []
        if history:
            for m in history:
                if m.role == "user":
                    lc_history.append(HumanMessage(content=m.content))
                else:
                    lc_history.append(AIMessage(content=m.content))

        log.info("ask_generating", tenant=tenant_slug, provider=self._llm_name, sources=len(search_resp.results))

        # Step 4: run the chain. ainvoke() is the async version of invoke().
        answer = await self._chain.ainvoke({
            "context": context,
            "question": question,
            "history": lc_history,
        })

        log.info("ask_complete", tenant=tenant_slug, answer_length=len(answer))
        return AskResponse(
            question=question,
            answer=answer,
            sources=search_resp.results,
            llm_provider=self._llm_name,
        )
