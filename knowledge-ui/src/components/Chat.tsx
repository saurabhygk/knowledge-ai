import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { HistoryMessage, Message, Tenant } from '../types'

interface Props { tenant: Tenant }

const ESCALATION_KEYWORDS = [
  'talk to agent', 'talk to a person', 'talk to someone', 'talk to human',
  'speak to agent', 'speak to a person', 'speak to someone', 'speak to human',
  'contact support', 'customer support', 'human agent', 'live agent',
  'real person', 'live chat', 'connect me', 'transfer me', 'escalate',
]

const NO_ANSWER_PHRASE = 'i could not find'

function isEscalationRequest(text: string) {
  const lower = text.toLowerCase()
  return ESCALATION_KEYWORDS.some(kw => lower.includes(kw))
}

function EscalationCard() {
  return (
    <div className="bg-white border border-emerald-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm max-w-[80%]">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-lg">🙋</span>
        <span className="font-semibold text-gray-800 text-sm">Connect with our Support Team</span>
      </div>
      <p className="text-xs text-gray-500 leading-relaxed">
        Our support team can help with questions not covered in the knowledge base.
        A representative will get back to you shortly.
      </p>
      <div className="mt-3 flex items-center gap-2 text-xs text-emerald-700 font-medium">
        <span>📬</span>
        <span>Support request noted — we'll be in touch.</span>
      </div>
    </div>
  )
}

function BotMessage({ msg }: { msg: Message }) {
  if (msg.escalate) return <EscalationCard />
  return (
    <div className="max-w-[80%]">
      <div className={`px-4 py-3 rounded-2xl rounded-tl-sm text-sm leading-relaxed shadow-sm
        ${msg.error ? 'bg-red-50 text-red-700' : 'bg-white border border-gray-200 text-gray-800'}`}>
        {msg.text}
      </div>
    </div>
  )
}

export default function Chat({ tenant }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', text: `Hi! I'm ready to answer questions about ${tenant.name}. Ask me anything.` },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    setMessages([{ role: 'bot', text: `Hi! I'm ready to answer questions about ${tenant.name}. Ask me anything.` }])
  }, [tenant.slug])

  const pushEscalationCard = () =>
    setMessages(prev => [...prev, { role: 'bot', text: '', escalate: true }])

  const send = async () => {
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: q }])

    // User is explicitly asking for a human — skip the LLM
    if (isEscalationRequest(q)) {
      setMessages(prev => [
        ...prev,
        { role: 'bot', text: 'Of course! Let me connect you with our support team.' },
      ])
      setTimeout(pushEscalationCard, 300)
      return
    }

    setLoading(true)
    try {
      const history: HistoryMessage[] = messages
        .filter(m => !m.error && !m.escalate)
        .slice(-10)
        .map(m => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text }))

      const res = await api.ask(tenant.slug, q, history)

      setMessages(prev => [...prev, {
        role: 'bot',
        text: res.answer,
        sources: res.sources,
        llm_provider: res.llm_provider,
      }])

      // If the bot couldn't find an answer, offer escalation automatically
      if (res.answer.toLowerCase().includes(NO_ANSWER_PHRASE)) {
        setTimeout(pushEscalationCard, 400)
      }
    } catch (e: unknown) {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: e instanceof Error ? e.message : 'Something went wrong.',
        error: true,
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
        {messages.map((msg, i) => (
          msg.role === 'user'
            ? (
              <div key={i} className="flex justify-end">
                <div className="bg-indigo-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm text-sm max-w-[75%] shadow-sm leading-relaxed">
                  {msg.text}
                </div>
              </div>
            )
            : (
              <div key={i} className="flex justify-start">
                <BotMessage msg={msg} />
              </div>
            )
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex gap-1.5 items-center">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-gray-200 bg-white px-4 py-3 flex gap-3 items-end">
        <textarea
          rows={1}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          placeholder="Ask a question about your documents…"
          className="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 max-h-32 leading-relaxed"
        />
        <button
          onClick={send}
          disabled={!input.trim() || loading}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-xl px-4 py-2.5 text-sm font-medium transition-colors shrink-0"
        >
          Send
        </button>
      </div>
    </div>
  )
}
