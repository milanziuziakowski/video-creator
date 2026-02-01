"""Add voices table.

Revision ID: 003_voices
Revises: 002_jwt_auth
Create Date: 2026-02-01 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_voices'
down_revision: Union[str, None] = '002_jwt_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create voices table
    op.create_table(
        'voices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('voice_id', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('voices')
