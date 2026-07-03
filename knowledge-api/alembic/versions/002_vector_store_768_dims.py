"""Resize vector_store embedding column to 768 dims for Ollama nomic-embed-text

Revision ID: 002
Revises: 001
Create Date: 2026-07-03 00:00:00.000000

Switch from 1536 (OpenAI text-embedding-3-small) to 768 (Ollama nomic-embed-text).
The VECTOR column dimension is fixed at creation time — changing it requires
dropping and recreating the column plus its index.
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_vector_store_hnsw")
    op.execute("ALTER TABLE vector_store DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE vector_store ADD COLUMN embedding VECTOR(768)")
    op.execute("""
        CREATE INDEX idx_vector_store_hnsw
            ON vector_store USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_vector_store_hnsw")
    op.execute("ALTER TABLE vector_store DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE vector_store ADD COLUMN embedding VECTOR(1536)")
    op.execute("""
        CREATE INDEX idx_vector_store_hnsw
            ON vector_store USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
    """)
