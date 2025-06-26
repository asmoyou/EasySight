"""添加用户消息表

创建时间: 2024-01-01
描述: 添加UserMessage表用于存储用户个人消息
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_user_messages'
down_revision = None  # 根据实际情况设置
branch_labels = None
depends_on = None

def upgrade():
    """创建用户消息表"""
    op.create_table(
        'user_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.Enum('info', 'warning', 'error', 'success', name='messagetype'), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('receiver_id', sa.Integer(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, default='general'),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # 创建索引
    op.create_index('idx_user_messages_receiver_id', 'user_messages', ['receiver_id'])
    op.create_index('idx_user_messages_is_read', 'user_messages', ['is_read'])
    op.create_index('idx_user_messages_created_at', 'user_messages', ['created_at'])
    op.create_index('idx_user_messages_category', 'user_messages', ['category'])
    op.create_index('idx_user_messages_message_type', 'user_messages', ['message_type'])

def downgrade():
    """删除用户消息表"""
    op.drop_index('idx_user_messages_message_type', table_name='user_messages')
    op.drop_index('idx_user_messages_category', table_name='user_messages')
    op.drop_index('idx_user_messages_created_at', table_name='user_messages')
    op.drop_index('idx_user_messages_is_read', table_name='user_messages')
    op.drop_index('idx_user_messages_receiver_id', table_name='user_messages')
    op.drop_table('user_messages')
    op.execute('DROP TYPE IF EXISTS messagetype')