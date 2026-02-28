"""add track layout columns

Revision ID: c3d9e7a1b2c4
Revises: b1f8a3c2d4e5
Create Date: 2026-02-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c3d9e7a1b2c4"
down_revision = "b1f8a3c2d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tracks", sa.Column("performers", sa.ARRAY(sa.Text()), nullable=True))
    op.add_column("tracks", sa.Column("layout_type", sa.String(length=20), nullable=False, server_default="track"))
    op.add_column("tracks", sa.Column("parent_track_id", sa.UUID(), nullable=True))
    op.add_column("tracks", sa.Column("layout_order", sa.Integer(), nullable=False, server_default="0"))

    op.create_foreign_key(
        "fk_tracks_parent_track_id_tracks",
        "tracks",
        "tracks",
        ["parent_track_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.execute("UPDATE tracks SET layout_type = 'track' WHERE layout_type IS NULL")
    op.execute(
        """
        WITH ordered AS (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY album_id ORDER BY side, position, created_at) - 1 AS sort_index
            FROM tracks
        )
        UPDATE tracks t
        SET layout_order = ordered.sort_index
        FROM ordered
        WHERE ordered.id = t.id
        """
    )

    op.alter_column("tracks", "layout_type", server_default=None)
    op.alter_column("tracks", "layout_order", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_tracks_parent_track_id_tracks", "tracks", type_="foreignkey")
    op.drop_column("tracks", "layout_order")
    op.drop_column("tracks", "parent_track_id")
    op.drop_column("tracks", "layout_type")
    op.drop_column("tracks", "performers")
