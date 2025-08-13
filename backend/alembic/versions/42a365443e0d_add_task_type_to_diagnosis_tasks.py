"""add_task_type_to_diagnosis_tasks

Revision ID: 42a365443e0d
Revises: 80936f0d9326
Create Date: 2025-08-07 14:27:04.238940

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '42a365443e0d'
down_revision = '80936f0d9326'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建TaskType枚举
    task_type_enum = sa.Enum('DIAGNOSIS', 'AI_DETECTION', 'MONITORING', 'MAINTENANCE', name='tasktype')
    task_type_enum.create(op.get_bind())
    
    # 添加task_type字段到diagnosis_tasks表
    op.add_column('diagnosis_tasks', sa.Column('task_type', task_type_enum, server_default='DIAGNOSIS', nullable=True))
    
    # 更新现有记录的默认值
    op.execute("UPDATE diagnosis_tasks SET task_type = 'DIAGNOSIS' WHERE task_type IS NULL")
    
    # 设置字段为非空
    op.alter_column('diagnosis_tasks', 'task_type', nullable=False)


def downgrade() -> None:
    # 删除task_type字段
    op.drop_column('diagnosis_tasks', 'task_type')
    
    # 删除TaskType枚举
    op.execute("DROP TYPE tasktype")