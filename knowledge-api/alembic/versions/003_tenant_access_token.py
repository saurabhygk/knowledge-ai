"""Add access_token column to tenants for per-tenant URL-based access control

Revision ID: 003
Revises: 002
Create Date: 2026-07-04 00:00:00.000000
"""
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE tenants ADD COLUMN access_token VARCHAR(64)")
    # Backfill existing tenants with a random token (md5 needs no extension)
    op.execute("UPDATE tenants SET access_token = md5(random()::text || clock_timestamp()::text || id::text) WHERE access_token IS NULL")
    op.execute("ALTER TABLE tenants ALTER COLUMN access_token SET NOT NULL")
    op.execute("CREATE UNIQUE INDEX idx_tenants_access_token ON tenants(access_token)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_tenants_access_token")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS access_token")
