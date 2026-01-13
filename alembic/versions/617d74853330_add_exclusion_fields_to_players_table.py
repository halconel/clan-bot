"""Add exclusion fields to players table

Revision ID: 617d74853330
Revises: cff86a05b80a
Create Date: 2026-01-12 22:21:14.146042

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "617d74853330"
down_revision = "cff86a05b80a"
branch_labels = None
depends_on = None


def upgrade():
    # Add exclusion fields to players table
    op.add_column("players", sa.Column("exclusion_date", sa.TIMESTAMP(), nullable=True))
    op.add_column("players", sa.Column("exclusion_reason", sa.Text(), nullable=True))
    op.add_column("players", sa.Column("excluded_by", sa.VARCHAR(length=255), nullable=True))

    # Add index on status column for better query performance
    op.create_index("idx_players_status", "players", ["status"])


def downgrade():
    # Drop index
    op.drop_index("idx_players_status", table_name="players")

    # Drop exclusion fields
    op.drop_column("players", "excluded_by")
    op.drop_column("players", "exclusion_reason")
    op.drop_column("players", "exclusion_date")
