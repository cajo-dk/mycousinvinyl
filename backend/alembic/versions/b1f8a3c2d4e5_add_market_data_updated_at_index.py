"""add market_data updated_at index

Revision ID: b1f8a3c2d4e5
Revises: 9834473fbd7a
Create Date: 2026-01-11 18:05:00.000000
"""

from alembic import op


revision = "b1f8a3c2d4e5"
down_revision = "9834473fbd7a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_market_data_updated_at ON market_data(updated_at);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_market_data_updated_at;")
