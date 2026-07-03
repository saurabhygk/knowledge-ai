"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS vector;

        CREATE TABLE IF NOT EXISTS tenants (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name       TEXT        NOT NULL,
            slug       TEXT        NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS documents (
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

        CREATE INDEX IF NOT EXISTS idx_documents_tenant_status ON documents (tenant_id, status);

        CREATE TABLE IF NOT EXISTS chunks (
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

        CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks (document_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_tenant   ON chunks (tenant_id);

        CREATE TABLE IF NOT EXISTS vector_store (
            id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content   TEXT,
            metadata  JSONB,
            embedding VECTOR(1536)
        );

        CREATE INDEX IF NOT EXISTS idx_vector_store_hnsw
            ON vector_store USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);

        INSERT INTO tenants (name, slug)
        VALUES ('Demo Tenant', 'demo')
        ON CONFLICT (slug) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS vector_store;
        DROP TABLE IF EXISTS chunks;
        DROP TABLE IF EXISTS documents;
        DROP TABLE IF EXISTS tenants;
        DROP EXTENSION IF EXISTS vector;
    """)
