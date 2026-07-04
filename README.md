# KnowledgeAI

A multi-tenant RAG (Retrieval-Augmented Generation) platform. Upload documents, have them automatically parsed, chunked, embedded, and stored in a vector database — then query them with natural language via a chat UI.

## Architecture

```
Browser
  │
  ▼
knowledge-ui  (React + Vite · port 5173)
  │  /admin        → password-protected admin panel (upload docs, manage tenants, copy share links)
  │  /chat/:slug   → public tenant chat (token-gated URL per client)
  │
  ▼
knowledge-api  (FastAPI · port 8080)
  │  POST /api/v1/tenants                          → create tenant (auto-generates access token)
  │  GET  /api/v1/tenants                          → list tenants
  │  GET  /api/v1/tenants/{slug}                   → get tenant by slug
  │  GET  /api/v1/tenants/{slug}/verify-token      → validate client access token
  │  POST /api/v1/tenants/{slug}/documents         → upload file
  │  GET  /api/v1/tenants/{slug}/documents         → list documents
  │  POST /api/v1/tenants/{slug}/search            → semantic search
  │  POST /api/v1/tenants/{slug}/ask               → RAG Q&A with conversation history
  │
  ├──► PostgreSQL  (tenants · documents · vector_store with pgvector)
  ├──► MinIO       (raw file storage)
  └──► Redis Streams  (event queue: knowledge-ai:document-processing)
              │
              ▼
        knowledge-processor  (Python worker)
              │  consumes stream → download → parse → chunk → embed → store
              │
              └──► PostgreSQL / pgvector  (vector_store embeddings)
```

## Services

| Service | Stack | Port | Purpose |
|---|---|---|---|
| `knowledge-ui` | React + Vite + TypeScript + Tailwind | 5173 | Admin panel + per-tenant public chat |
| `knowledge-api` | Python / FastAPI | 8080 | REST API — tenants, documents, search, RAG |
| `knowledge-processor` | Python worker | — | Async pipeline — parse, chunk, embed, index |

---

## Local Development

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Node.js 18+
- An OpenAI API key **or** [Ollama](https://ollama.com) running locally

### 1. Start infrastructure

```bash
docker compose up postgres redis minio -d
```

### 2. Run knowledge-api

```bash
cd knowledge-api

cp .env.example .env
# Edit .env — set EMBEDDING_PROVIDER, LLM_PROVIDER, and API keys

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

alembic upgrade head               # runs all migrations including access_token column

uvicorn app.main:app --reload --port 8080
```

API live at **http://localhost:8080** · Interactive docs: **http://localhost:8080/docs**

### 3. Run knowledge-processor

```bash
cd knowledge-processor

cp .env.example .env
# Edit .env — set EMBEDDING_PROVIDER and matching API key / Ollama URL

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m app.main      # starts the Redis Stream consumer loop
```

### 4. Run knowledge-ui

```bash
cd knowledge-ui

cp .env.example .env
# Edit .env — set VITE_ADMIN_PASSWORD

npm install
npm run dev
```

UI live at **http://localhost:5173**

---

## Multi-Tenant Access Model

Each tenant (client) has an isolated knowledge base and a unique access-controlled chat URL.

### Admin workflow

1. Go to `/admin` and log in with the admin password
2. Create a tenant — a random access token is generated automatically
3. Upload documents via the **File Upload** tab
4. Copy the share link from the banner:
   ```
   http://your-domain.com/chat/my-company?token=a3f9b2...
   ```
5. Send the link to your client's users

### Client / end-user access

Users open the link provided by the admin. The token in the URL is validated before the chat loads:

| Scenario | Result |
|---|---|
| Valid token | Chat interface loads |
| Invalid / tampered token | 🔒 "Invalid or expired access token" |
| No token in URL | 🔒 "Access token required" |

### Escalation to support agent

The chat automatically offers a support escalation card in two cases:

- User explicitly asks (e.g. *"talk to agent"*, *"speak to someone"*, *"contact support"*)
- Bot responds with "I could not find a clear answer"

The card currently shows a contact prompt. A live chat integration (Crisp, Intercom, Zendesk) can be wired in later by updating the `EscalationCard` component in `knowledge-ui/src/components/Chat.tsx`.

---

## Conversation Context

The `/ask` endpoint accepts a `history` array so the LLM can reference earlier turns in the same session. The UI automatically sends the last 10 messages (5 turns) with each request.

```json
{
  "question": "Can you summarise that?",
  "history": [
    { "role": "user", "content": "What is the leave policy?" },
    { "role": "assistant", "content": "Employees are entitled to..." }
  ],
  "top_k": 5,
  "min_score": 0.5
}
```

---

## Embedding & LLM Providers

Switch providers by changing `.env` — no code changes needed. The processor auto-resizes the vector column if embedding dimensions change.

### knowledge-api `.env`

```env
# Embedding: openai (1536 dims) or ollama (768 dims)
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# LLM for /ask: ollama or openai
LLM_PROVIDER=ollama
OLLAMA_CHAT_MODEL=llama3.2

# OpenAI (if using openai for either)
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
```

### Ollama setup (local, free)

```bash
ollama pull nomic-embed-text   # embeddings
ollama pull llama3.2           # chat
```

---

## API Reference

### Tenants

```bash
# Create a tenant
curl -X POST http://localhost:8080/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "My Company", "slug": "my-company"}'

# List tenants
curl http://localhost:8080/api/v1/tenants

# Get tenant by slug
curl http://localhost:8080/api/v1/tenants/my-company

# Validate access token
curl "http://localhost:8080/api/v1/tenants/my-company/verify-token?token=abc123"
```

### Documents

```bash
# Upload a document
curl -X POST http://localhost:8080/api/v1/tenants/my-company/documents \
  -F "file=@/path/to/document.pdf"

# List documents
curl "http://localhost:8080/api/v1/tenants/my-company/documents?page=1&size=20"
```

### Ask a question (RAG)

```bash
curl -X POST http://localhost:8080/api/v1/tenants/my-company/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key findings?",
    "history": [],
    "top_k": 5,
    "min_score": 0.5
  }'
```

### Semantic search

```bash
curl -X POST http://localhost:8080/api/v1/tenants/my-company/search \
  -H "Content-Type: application/json" \
  -d '{"query": "quarterly revenue", "top_k": 5, "min_score": 0.5}'
```

### Health check

```bash
curl http://localhost:8080/health
# {"status":"ok"}
```

---

## Document Status Flow

```
UPLOADED → PROCESSING → INDEXED
                    └──► FAILED  (error_message populated)
```

Documents are polled every 4 seconds in the admin UI until they reach `INDEXED` or `FAILED`.

---

## Configuration

### knowledge-api (`knowledge-api/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://knowledgeai:secret@localhost:5432/knowledgeai` | Postgres connection |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO host:port |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO secret key |
| `EMBEDDING_PROVIDER` | `openai` | `openai` or `ollama` |
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OPENAI_API_KEY` | — | Required if using OpenAI |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` |
| `PORT` | `8080` | API listen port |

### knowledge-ui (`knowledge-ui/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8080` | API base URL |
| `VITE_ADMIN_PASSWORD` | `admin` | Admin panel password — change before deploying |

---

## Production Deployment

### Run everything with Docker Compose

```bash
export OPENAI_API_KEY=sk-...   # if using OpenAI

docker compose up --build -d
```

The `knowledge-api` container runs `alembic upgrade head` automatically before starting.

### Production checklist

- Replace all default passwords (`secret`, `minioadmin`, `VITE_ADMIN_PASSWORD`) with strong values
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault) for API keys
- Put `knowledge-api` behind a reverse proxy (nginx, Caddy, ALB) for TLS termination
- Build the UI for production and serve as static files:
  ```bash
  cd knowledge-ui && npm run build   # outputs to knowledge-ui/dist/
  ```
- Set `LOG_LEVEL=INFO` in production
- Scale uvicorn workers: `--workers $(( 2 * $(nproc) ))`
- Run migrations as a pre-deploy step:
  ```bash
  docker run --rm \
    -e DATABASE_URL=postgresql://user:pass@host:5432/knowledgeai \
    knowledgeai-api:latest \
    alembic upgrade head
  ```

### Future: per-user authentication

The current access model uses per-tenant tokens shared with all users of that client. The architecture is designed to extend to per-user auth (Google SSO, username/password) — the hook is in `ChatPage.tsx`'s `validate()` function. When user auth is added, replace `api.verifyToken()` with your auth flow; the rest of the page stays the same.
