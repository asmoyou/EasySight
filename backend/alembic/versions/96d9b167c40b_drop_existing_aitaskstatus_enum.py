"""Drop existing aitaskstatus enum

Revision ID: 96d9b167c40b
Revises: 8fb51b3973c9
Create Date: 2025-08-08 12:11:10.322654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96d9b167c40b'
down_revision = '42a365443e0d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 删除现有的aitaskstatus枚举类型（如果存在）
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'aitaskstatus'"))
    if result.fetchone():
        connection.execute(sa.text("DROP TYPE aitaskstatus CASCADE"))


def downgrade() -> None:
    # 重新创建aitaskstatus枚举类型
    ai_task_status_enum = sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='aitaskstatus')
    ai_task_status_enum.create(op.get_bind())