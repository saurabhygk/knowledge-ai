# KnowledgeAI

A multi-tenant RAG (Retrieval-Augmented Generation) platform. Upload documents, have them automatically parsed, chunked, embedded, and stored in a vector database — then query them with semantic search.

## Architecture

```
Client
  │
  ▼
knowledge-api  (FastAPI · port 8080)
  │  POST /api/v1/tenants/{slug}/documents  → upload file → MinIO, DB record, Redis event
  │  GET  /api/v1/tenants/{slug}/documents  → paginated document list
  │  GET  /api/v1/tenants/{slug}/documents/{id} → document detail
  │
  ├──► PostgreSQL  (tenants · documents · chunks tables + pgvector)
  ├──► MinIO       (raw file storage)
  └──► Redis Streams  (event queue: knowledge-ai:document-processing)
              │
              ▼
        knowledge-processor  (Python worker)
              │  consumes stream → download → parse → chunk → embed → store
              │
              ├──► PostgreSQL  (status updates, chunks)
              └──► PostgreSQL/pgvector  (vector_store embeddings)
```

## Services

| Service | Stack | Port | Purpose |
|---|---|---|---|
| `knowledge-api` | Python / FastAPI | 8080 | REST API — document upload & management |
| `knowledge-processor` | Python worker | — | Async pipeline — parsing, chunking, embedding |

---

## Local Development

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- An OpenAI API key (for embeddings in the processor)

### 1. Start infrastructure

```bash
docker compose up postgres redis minio -d
```

Wait for services to be healthy:

```bash
docker compose ps
```

### 2. Run knowledge-api

```bash
cd knowledge-api

# Copy and review environment config
cp .env.example .env

# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API (with hot reload)
uvicorn app.main:app --reload --port 8080
```

API is live at **http://localhost:8080**
Interactive docs: **http://localhost:8080/docs**

### 3. Run knowledge-processor

```bash
cd knowledge-processor

cp .env.example .env
# Edit .env — set OPENAI_API_KEY (or switch EMBEDDING_PROVIDER=ollama)

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m app.main      # starts the Redis Stream consumer loop
```

---

## API Reference

All document routes are tenant-scoped. A `demo` tenant is seeded automatically by migrations.

### Upload a document

```bash
curl -X POST http://localhost:8080/api/v1/tenants/demo/documents \
  -F "file=@/path/to/document.pdf"
```

**Response `202 Accepted`:**
```json
{
  "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "UPLOADED",
  "message": "Document uploaded and queued for processing"
}
```

### List documents

```bash
curl "http://localhost:8080/api/v1/tenants/demo/documents?page=1&size=20"
```

**Response:**
```json
{
  "items": [
    {
      "id": "3fa85f64-...",
      "tenant_id": "...",
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "status": "INDEXED",
      "metadata": {},
      "error_message": null,
      "created_at": "2025-01-01T00:00:00Z",
      "indexed_at": "2025-01-01T00:01:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

### Get a single document

```bash
curl http://localhost:8080/api/v1/tenants/demo/documents/3fa85f64-5717-4562-b3fc-2c963f66afa6
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
                    └──► FAILED (error_message is populated)
```

The processor transitions document status as it works through each pipeline stage.

---

## Configuration

### knowledge-api (`knowledge-api/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://knowledgeai:secret@localhost:5432/knowledgeai` | Postgres connection |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `REDIS_STREAM` | `knowledge-ai:document-processing` | Stream key |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO host:port |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO secret key |
| `MINIO_BUCKET` | `knowledge-ai-docs` | Bucket name |
| `LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` |
| `PORT` | `8080` | API listen port |

### knowledge-processor (`knowledge-processor/.env`)

See `knowledge-processor/.env.example` — includes embedding provider, chunking strategy, and OpenAI/Ollama settings.

---

## Production Deployment

### Run everything with Docker Compose

```bash
# Pass real secrets as env vars — never use .env.example in prod
export OPENAI_API_KEY=sk-...

docker compose up --build -d
```

This builds and starts all services. The `knowledge-api` container automatically runs `alembic upgrade head` before uvicorn starts.

### Production checklist

- Replace all default passwords (`secret`, `minioadmin`) with strong credentials
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault) for `OPENAI_API_KEY`
- Put `knowledge-api` behind a reverse proxy (nginx, Caddy, ALB) for TLS termination
- Set `LOG_LEVEL=INFO` (not DEBUG) in production
- Scale uvicorn workers: set `--workers` to `2 × CPU cores`
- Run migrations as a pre-deploy step for zero-downtime deploys:

```bash
docker run --rm \
  -e DATABASE_URL=postgresql://user:pass@host:5432/knowledgeai \
  knowledgeai-api:latest \
  alembic upgrade head
```

### Override config per environment

Use a `docker-compose.prod.yml` override file:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
