"""initial_core_schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-05

Core tables only: users, temple_members, donors, announcements
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table (Identity)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('roles', postgresql.ARRAY(sa.String()), nullable=False, server_default='{"GENERAL_USER"}'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create temple_members table (Entity - linked to User optionally)
    op.create_table('temple_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(50), nullable=False),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('position', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_temple_members_id', 'temple_members', ['id'])

    # Create donors table (Entity - standalone)
    op.create_table('donors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('phone', sa.String(32), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('pan_number', sa.String(20), nullable=True),
        sa.Column('donated_for', sa.String(100), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('donated_on', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_donors_id', 'donors', ['id'])

    # Create announcements table (with audit FK to users)
    op.create_table('announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'])
    )
    op.create_index('ix_announcements_id', 'announcements', ['id'])


def downgrade() -> None:
    op.drop_table('announcements')
    op.drop_table('donors')
    op.drop_table('temple_members')
    op.drop_table('users')
