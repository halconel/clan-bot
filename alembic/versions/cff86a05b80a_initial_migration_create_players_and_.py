"""Initial migration: create players and pending_registrations tables

Revision ID: cff86a05b80a
Revises: 
Create Date: 2026-01-12 22:14:09.404877

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cff86a05b80a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create players table
    op.create_table(
        'players',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BIGINT(), nullable=False),
        sa.Column('username', sa.VARCHAR(length=255), nullable=False),
        sa.Column('nickname', sa.VARCHAR(length=100), nullable=False),
        sa.Column('screenshot_path', sa.VARCHAR(length=500), nullable=True),
        sa.Column('registration_date', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('status', sa.VARCHAR(length=50), server_default='Активен', nullable=False),
        sa.Column('added_by', sa.VARCHAR(length=255), server_default='bot', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index('idx_players_telegram_id', 'players', ['telegram_id'])
    op.create_index('idx_players_username', 'players', ['username'])

    # Create pending_registrations table
    op.create_table(
        'pending_registrations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BIGINT(), nullable=False),
        sa.Column('username', sa.VARCHAR(length=255), nullable=False),
        sa.Column('nickname', sa.VARCHAR(length=100), nullable=False),
        sa.Column('screenshot_path', sa.VARCHAR(length=500), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index('idx_pending_telegram_id', 'pending_registrations', ['telegram_id'])
    op.create_index('idx_pending_username', 'pending_registrations', ['username'])


def downgrade():
    # Drop pending_registrations table
    op.drop_index('idx_pending_username', table_name='pending_registrations')
    op.drop_index('idx_pending_telegram_id', table_name='pending_registrations')
    op.drop_table('pending_registrations')

    # Drop players table
    op.drop_index('idx_players_username', table_name='players')
    op.drop_index('idx_players_telegram_id', table_name='players')
    op.drop_table('players')
