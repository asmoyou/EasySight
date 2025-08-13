"""Add missing status column to ai_tasks

Revision ID: d74a5e212bbf
Revises: 8fb51b3973c9
Create Date: 2025-08-08 12:14:20.671773

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd74a5e212bbf'
down_revision = '8fb51b3973c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加缺失的status列到ai_tasks表
    ai_task_status_enum = sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='aitaskstatus')
    op.add_column('ai_tasks', sa.Column('status', ai_task_status_enum, nullable=False, server_default='PENDING', comment='任务状态'))


def downgrade() -> None:
    # 删除status列
    op.drop_column('ai_tasks', 'status')