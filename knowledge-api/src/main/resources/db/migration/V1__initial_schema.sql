-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Tenants
CREATE TABLE tenants (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       TEXT        NOT NULL,
    slug       TEXT        NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Documents
CREATE TABLE documents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID        NOT NULL REFERENCES tenants (id),
    filename      TEXT        NOT NULL,
    content_type  TEXT,
    storage_key   TEXT        NOT NULL,
    status        TEXT        NOT NULL DEFAULT 'UPLOADED'
                      CHECK (status IN ('UPLOADED', 'PROCESSING', 'INDEXED', 'FAILED')),
    metadata      JSONB       NOT NULL DEFAULT '{}',
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    indexed_at    TIMESTAMPTZ
);

CREATE INDEX idx_documents_tenant_status ON documents (tenant_id, status);

-- Chunks
CREATE TABLE chunks (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID    NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    tenant_id   UUID    NOT NULL REFERENCES tenants (id),
    chunk_index INTEGER NOT NULL,
    text        TEXT    NOT NULL,
    char_start  INTEGER,
    char_end    INTEGER,
    metadata    JSONB   NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_document ON chunks (document_id);
CREATE INDEX idx_chunks_tenant   ON chunks (tenant_id);

-- Spring AI PGVector store table
CREATE TABLE IF NOT EXISTS vector_store (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content   TEXT,
    metadata  JSONB,
    embedding VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS idx_vector_store_hnsw
    ON vector_store USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Seed: default tenant for local development
INSERT INTO tenants (name, slug) VALUES ('Demo Tenant', 'demo');
