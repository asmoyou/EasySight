"""Add zlm_port to MediaProxy

Revision ID: d836fcc93aa6
Revises: 90d1649e32ce
Create Date: 2025-06-27 17:08:50.051415

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd836fcc93aa6'
down_revision = '90d1649e32ce'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('media_proxies', sa.Column('zlm_port', sa.Integer(), nullable=False, comment='ZLMediaKit端口', server_default='8060'))
    op.alter_column('media_proxies', 'port',
               existing_type=sa.INTEGER(),
               comment='流媒体服务端口',
               existing_comment='节点端口',
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('media_proxies', 'port',
               existing_type=sa.INTEGER(),
               comment='节点端口',
               existing_comment='流媒体服务端口',
               existing_nullable=False)
    op.drop_column('media_proxies', 'zlm_port')
    # ### end Alembic commands ###