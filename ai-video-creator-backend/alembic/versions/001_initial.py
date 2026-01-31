"""Initial database schema.

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('azure_oid', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('story_prompt', sa.Text(), nullable=True),
        sa.Column('target_duration_sec', sa.Integer(), nullable=False, default=60),
        sa.Column('status', sa.String(50), nullable=False, default='draft'),
        sa.Column('first_frame_url', sa.Text(), nullable=True),
        sa.Column('audio_sample_url', sa.Text(), nullable=True),
        sa.Column('voice_id', sa.String(255), nullable=True),
        sa.Column('final_video_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create segments table
    op.create_table(
        'segments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('index', sa.Integer(), nullable=False),
        sa.Column('video_prompt', sa.Text(), nullable=True),
        sa.Column('narration_text', sa.Text(), nullable=True),
        sa.Column('end_frame_prompt', sa.Text(), nullable=True),
        sa.Column('duration_sec', sa.Integer(), nullable=False, default=6),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('approved', sa.Boolean(), nullable=False, default=False),
        sa.Column('first_frame_url', sa.Text(), nullable=True),
        sa.Column('last_frame_url', sa.Text(), nullable=True),
        sa.Column('video_task_id', sa.String(255), nullable=True),
        sa.Column('audio_task_id', sa.String(255), nullable=True),
        sa.Column('video_url', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('muxed_video_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create unique constraint for segment index within project
    op.create_index('ix_segments_project_index', 'segments', ['project_id', 'index'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_segments_project_index', 'segments')
    op.drop_table('segments')
    op.drop_table('projects')
    op.drop_table('users')
