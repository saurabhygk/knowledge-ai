# KnowledgeAI

A multi-tenant RAG (Retrieval-Augmented Generation) platform. Upload documents, have them automatically parsed, chunked, embedded, and stored in a vector database — then query them with natural language via a chat UI.

## Architecture

```
Browser
  │
  ▼
knowledge-ui  (React + Vite · port 5173)
  │  Chat interface — ask questions, get answers from your documents
  │  Documents tab — upload files, track processing status
  │
  ▼
knowledge-api  (FastAPI · port 8080)
  │  POST /api/v1/tenants                        → create tenant
  │  GET  /api/v1/tenants                        → list tenants
  │  POST /api/v1/tenants/{slug}/documents       → upload file
  │  GET  /api/v1/tenants/{slug}/documents       → list documents
  │  POST /api/v1/tenants/{slug}/search          → semantic search
  │  POST /api/v1/tenants/{slug}/ask             → RAG question answering
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
| `knowledge-ui` | React + Vite + TypeScript + Tailwind | 5173 | Chat UI — ask questions, upload documents |
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

# Copy and review environment config
cp .env.example .env
# Edit .env — set EMBEDDING_PROVIDER, LLM_PROVIDER, and API keys

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API (with hot reload)
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

npm install
npm run dev
```

UI live at **http://localhost:5173**

---

## Embedding & LLM Providers

Switch providers by editing `.env` — no code changes needed. The processor auto-resizes the vector column if dimensions change.

### knowledge-api `.env`

```env
# Embedding: openai (1536 dims) or ollama (768 dims)
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# LLM for /ask endpoint: ollama or openai
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
  -d '{"question": "What are the key findings?", "top_k": 5, "min_score": 0.5}'
```

**Response:**
```json
{
  "question": "What are the key findings?",
  "answer": "The key findings are...",
  "sources": [...],
  "llm_provider": "ollama"
}
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

---

## Production Deployment

### Run everything with Docker Compose

```bash
export OPENAI_API_KEY=sk-...   # if using OpenAI

docker compose up --build -d
```

The `knowledge-api` container runs `alembic upgrade head` automatically before starting.

### Production checklist

- Replace all default passwords (`secret`, `minioadmin`) with strong credentials
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault) for API keys
- Put `knowledge-api` behind a reverse proxy (nginx, Caddy, ALB) for TLS termination
- Build the UI for production and serve as static files: `npm run build` in `knowledge-ui/`
- Set `LOG_LEVEL=INFO` in production
- Scale uvicorn workers: `--workers $(( 2 * $(nproc) ))`
- Run migrations as a pre-deploy step:

```bash
docker run --rm \
  -e DATABASE_URL=postgresql://user:pass@host:5432/knowledgeai \
  knowledgeai-api:latest \
  alembic upgrade head
```
