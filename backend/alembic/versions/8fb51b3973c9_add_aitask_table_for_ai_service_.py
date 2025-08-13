"""Add AITask table for AI service detection tasks

Revision ID: 8fb51b3973c9
Revises: 42a365443e0d
Create Date: 2025-08-08 01:29:08.233735

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8fb51b3973c9'
down_revision = '96d9b167c40b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建AITaskStatus枚举（如果不存在）
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'aitaskstatus'"))
    if not result.fetchone():
        ai_task_status_enum = sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='aitaskstatus')
        ai_task_status_enum.create(connection)
    
    # 获取枚举类型引用
    ai_task_status_enum = sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='aitaskstatus')
    
    # 创建ai_tasks表
    op.create_table('ai_tasks',
        sa.Column('id', sa.Integer(), nullable=False, comment='任务ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='任务名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='任务描述'),
        sa.Column('service_id', sa.Integer(), nullable=False, comment='AI服务ID'),
        sa.Column('camera_id', sa.Integer(), nullable=False, comment='摄像头ID'),
        sa.Column('algorithm_id', sa.Integer(), nullable=False, comment='算法ID'),
        sa.Column('model_id', sa.Integer(), nullable=True, comment='模型ID'),
        sa.Column('detection_config', sa.JSON(), nullable=True, comment='检测配置'),
        sa.Column('roi_areas', sa.JSON(), nullable=True, comment='ROI区域配置'),
        sa.Column('alarm_threshold', sa.Float(), nullable=True, comment='告警阈值'),
        sa.Column('schedule_type', sa.String(length=50), nullable=True, comment='调度类型'),
        sa.Column('schedule_config', sa.JSON(), nullable=True, comment='调度配置'),
        sa.Column('interval_seconds', sa.Integer(), nullable=True, comment='执行间隔(秒)'),
        sa.Column('status', ai_task_status_enum, nullable=False, server_default='PENDING', comment='任务状态'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true', comment='是否激活'),
        sa.Column('assigned_worker', sa.String(length=100), nullable=True, comment='分配的worker节点ID'),
        sa.Column('total_runs', sa.Integer(), nullable=True, server_default='0', comment='总运行次数'),
        sa.Column('success_runs', sa.Integer(), nullable=True, server_default='0', comment='成功运行次数'),
        sa.Column('failed_runs', sa.Integer(), nullable=True, server_default='0', comment='失败运行次数'),
        sa.Column('last_run_time', postgresql.TIMESTAMP(timezone=True), nullable=True, comment='最后运行时间'),
        sa.Column('next_run_time', postgresql.TIMESTAMP(timezone=True), nullable=True, comment='下次运行时间'),
        sa.Column('avg_processing_time', sa.Float(), nullable=True, comment='平均处理时间(秒)'),
        sa.Column('total_detections', sa.Integer(), nullable=True, server_default='0', comment='总检测次数'),
        sa.Column('total_alarms', sa.Integer(), nullable=True, server_default='0', comment='总告警次数'),
        sa.Column('last_detection_time', postgresql.TIMESTAMP(timezone=True), nullable=True, comment='最后检测时间'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['service_id'], ['ai_services.id'], name='ai_tasks_service_id_fkey'),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], name='ai_tasks_camera_id_fkey'),
        sa.ForeignKeyConstraint(['algorithm_id'], ['ai_algorithms.id'], name='ai_tasks_algorithm_id_fkey'),
        sa.ForeignKeyConstraint(['model_id'], ['ai_models.id'], name='ai_tasks_model_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='ai_tasks_pkey')
    )
    
    # 创建索引
    op.create_index('ix_ai_tasks_id', 'ai_tasks', ['id'], unique=False)
    op.create_index('ix_ai_tasks_name', 'ai_tasks', ['name'], unique=False)
    op.create_index('ix_ai_tasks_status', 'ai_tasks', ['status'], unique=False)
    op.create_index('ix_ai_tasks_service_id', 'ai_tasks', ['service_id'], unique=False)
    op.create_index('ix_ai_tasks_camera_id', 'ai_tasks', ['camera_id'], unique=False)
    
    # 添加task_id字段到ai_service_logs表
    op.add_column('ai_service_logs', sa.Column('task_id', sa.Integer(), nullable=True, comment='AI任务ID'))
    op.create_foreign_key('ai_service_logs_task_id_fkey', 'ai_service_logs', 'ai_tasks', ['task_id'], ['id'])
    
    # 更新其他字段的注释
    op.alter_column('ai_models', 'inference_time',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               comment='推理时间(ms)',
               existing_nullable=True)
    op.alter_column('ai_models', 'tags',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               comment='标签列表',
               existing_nullable=True,
               existing_server_default=sa.text("'[]'::json"))
    op.alter_column('ai_models', 'description',
               existing_type=sa.TEXT(),
               comment='模型描述',
               existing_nullable=True)
    op.alter_column('diagnosis_tasks', 'task_type',
               existing_type=postgresql.ENUM('DIAGNOSIS', 'AI_DETECTION', 'MONITORING', 'MAINTENANCE', name='tasktype'),
               nullable=True,
               comment='任务类型',
               existing_server_default=sa.text("'DIAGNOSIS'::tasktype"))
    op.alter_column('diagnosis_tasks', 'assigned_worker',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=100),
               comment='分配的worker节点ID',
               existing_comment='分配的Worker节点ID',
               existing_nullable=True)


def downgrade() -> None:
    # 删除外键约束
    op.drop_constraint('ai_service_logs_task_id_fkey', 'ai_service_logs', type_='foreignkey')
    op.drop_column('ai_service_logs', 'task_id')
    
    # 删除索引
    op.drop_index('ix_ai_tasks_camera_id', table_name='ai_tasks')
    op.drop_index('ix_ai_tasks_service_id', table_name='ai_tasks')
    op.drop_index('ix_ai_tasks_status', table_name='ai_tasks')
    op.drop_index('ix_ai_tasks_name', table_name='ai_tasks')
    op.drop_index('ix_ai_tasks_id', table_name='ai_tasks')
    
    # 删除ai_tasks表
    op.drop_table('ai_tasks')
    
    # 删除AITaskStatus枚举
    op.execute("DROP TYPE aitaskstatus")
    
    # 恢复其他字段的修改
    op.alter_column('diagnosis_tasks', 'assigned_worker',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=255),
               comment='分配的Worker节点ID',
               existing_comment='分配的worker节点ID',
               existing_nullable=True)
    op.alter_column('diagnosis_tasks', 'task_type',
               existing_type=postgresql.ENUM('DIAGNOSIS', 'AI_DETECTION', 'MONITORING', 'MAINTENANCE', name='tasktype'),
               nullable=False,
               comment=None,
               existing_comment='任务类型',
               existing_server_default=sa.text("'DIAGNOSIS'::tasktype"))
    op.alter_column('ai_models', 'description',
               existing_type=sa.TEXT(),
               comment=None,
               existing_comment='模型描述',
               existing_nullable=True)
    op.alter_column('ai_models', 'tags',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               comment=None,
               existing_comment='标签列表',
               existing_nullable=True,
               existing_server_default=sa.text("'[]'::json"))
    op.alter_column('ai_models', 'inference_time',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               comment=None,
               existing_comment='推理时间(ms)',
               existing_nullable=True)