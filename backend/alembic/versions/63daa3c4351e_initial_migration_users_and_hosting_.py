"""Initial migration: users and hosting tables

Revision ID: 63daa3c4351e
Revises: 
Create Date: 2025-06-09 09:29:10.560779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "63daa3c4351e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """테이블 생성"""
    # Users 테이블 생성
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Hosting 테이블 생성
    op.create_table(
        'hosting',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vm_id', sa.String(length=100), nullable=False),
        sa.Column('vm_ip', sa.String(length=15), nullable=False),
        sa.Column('ssh_port', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='creating'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('vm_id'),
        sa.UniqueConstraint('ssh_port')
    )
    op.create_index('ix_hosting_id', 'hosting', ['id'], unique=False)
    op.create_index('ix_hosting_vm_id', 'hosting', ['vm_id'], unique=True)


def downgrade() -> None:
    """테이블 삭제"""
    # 인덱스 삭제
    op.drop_index('ix_hosting_vm_id', table_name='hosting')
    op.drop_index('ix_hosting_id', table_name='hosting')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    
    # 테이블 삭제
    op.drop_table('hosting')
    op.drop_table('users')
