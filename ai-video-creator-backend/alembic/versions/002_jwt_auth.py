"""Update users table for JWT auth.

Revision ID: 002_jwt_auth
Revises: 001_initial
Create Date: 2026-02-01

This migration updates the users table to support JWT-based authentication
instead of Azure Entra ID authentication.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_jwt_auth'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update users table for JWT authentication."""
    # Add new columns for JWT auth
    op.add_column('users', sa.Column('username', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('hashed_password', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True, default=True))
    
    # Create unique index on username
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    
    # For existing data: set username from email (before @ part)
    # This is handled in code - existing users will need to be migrated manually
    # or the database can be recreated for fresh installations
    
    # Note: We keep azure_oid column for now to support migration
    # It can be dropped in a future migration after all users have migrated


def downgrade() -> None:
    """Revert to Azure Entra ID authentication schema."""
    op.drop_index('ix_users_username', table_name='users')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'username')
