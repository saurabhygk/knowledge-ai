# KnowledgeAI

A multi-tenant RAG (Retrieval-Augmented Generation) platform. Upload documents, have them automatically parsed, chunked, embedded, and stored in a vector database — then query them with semantic search.

## Architecture

```
Client
  │
  ▼
knowledge-api (FastAPI, port 8080)
  │  POST /upload → stores file to MinIO, writes DB record, publishes Redis Stream event
  │  GET  /documents → paginated document list
  │  GET  /documents/{id} → document detail
  │
  ├──► PostgreSQL (documents, tenants, chunks tables)
  ├──► MinIO (raw file storage)
  └──► Redis Streams (event queue)
         │
         ▼
   knowledge-processor (Python worker)
         │  consumes Redis Stream events
         │  download → parse → chunk → embed → store
         │
         ├──► PostgreSQL (updates document status, saves chunks)
         └──► PostgreSQL/pgvector (saves embeddings to vector_store)
```

## Services

| Service | Language | Port | Purpose |
|---|---|---|---|
| `knowledge-api` | Python / FastAPI | 8080 | REST API — document upload & management |
| `knowledge-processor` | Python | 8001 | Background worker — parsing, chunking, embedding |

## Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local dev without Docker)
- An OpenAI API key (for embeddings)

---

## Local Development

### 1. Start infrastructure

```bash
docker compose up postgres redis minio qdrant -d
```

Wait for healthchecks to pass:
```bash
docker compose ps
```

### 2. Set up knowledge-api

```bash
cd knowledge-api
cp .env.example .env
# Edit .env if needed (defaults work with docker-compose infra)

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run DB migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload --port 8080
```

The API is now available at `http://localhost:8080`.
Interactive docs: `http://localhost:8080/docs`

### 3. Set up knowledge-processor

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

## API Endpoints

All document routes are scoped to a tenant. A `demo` tenant is seeded automatically.

### Upload a document

```bash
curl -X POST http://localhost:8080/api/v1/tenants/demo/documents \
  -F "file=@/path/to/document.pdf"
```

Response (`202 Accepted`):
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

Response:
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

### Get a document

```bash
curl http://localhost:8080/api/v1/tenants/demo/documents/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

### Health check

```bash
curl http://localhost:8080/health
# {"status": "ok"}
```

---

## Document Status Flow

```
UPLOADED → PROCESSING → INDEXED
                    └──► FAILED
```

The processor transitions the status as it works through each document.

---

## Configuration

Both services read configuration from environment variables (or a `.env` file).

### knowledge-api

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://knowledgeai:secret@localhost:5432/knowledgeai` | Postgres connection |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `REDIS_STREAM` | `knowledge-ai:document-processing` | Stream name |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO endpoint |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO secret key |
| `MINIO_BUCKET` | `knowledge-ai-docs` | Bucket name |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PORT` | `8080` | Server port |

### knowledge-processor

See `knowledge-processor/.env.example` for the full list including embedding provider and chunking settings.

---

## Production Deployment

### Build and run with Docker Compose

```bash
# Set secrets as real env vars (don't use .env.example in prod)
export OPENAI_API_KEY=sk-...

docker compose up --build -d
```

This starts all services including `knowledge-api` (port 8080) and `knowledge-processor`.

### Production checklist

- Replace default Postgres/MinIO credentials
- Set `LOG_LEVEL=INFO` (not DEBUG)
- Mount a persistent volume for Postgres data (already in docker-compose.yml)
- Put `knowledge-api` behind a reverse proxy (nginx/Caddy) for TLS termination
- Set `workers` in uvicorn proportional to CPU cores (default: 2)
- Use a secrets manager (AWS Secrets Manager, Vault) instead of env var plaintext for `OPENAI_API_KEY`

### Custom docker-compose for production

Create a `docker-compose.prod.yml` that overrides credentials and resource limits:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Database migrations

Migrations run automatically on container start (`alembic upgrade head`). For zero-downtime deploys, run migrations as a separate pre-deploy step:

```bash
docker run --rm \
  -e DATABASE_URL=postgresql://... \
  knowledgeai-api:latest \
  alembic upgrade head
```
