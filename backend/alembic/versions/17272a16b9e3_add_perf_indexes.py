"""add perf indexes

Revision ID: 17272a16b9e3
Revises: c9d6a755157f
Create Date: 2026-10-15 11:14:23.694893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17272a16b9e3'
down_revision: Union[str, Sequence[str], None] = 'c9d6a755157f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes."""
    # messages: 按会话 + 时间倒序查历史，最常用
    op.create_index(
        'ix_messages_session_created',
        'messages',
        ['session_id', sa.text('created_at DESC')],
    )
    # reports: 按用户 + 类型 + 时间查列表
    op.create_index(
        'ix_reports_user_kind_created',
        'reports',
        ['user_id', 'kind', sa.text('created_at DESC')],
    )
    # daily_logs: 按用户 + 时间倒序查打卡
    op.create_index(
        'ix_daily_logs_user_date_desc',
        'daily_logs',
        ['user_id', sa.text('log_date DESC')],
    )


def downgrade() -> None:
    """Drop performance indexes."""
    op.drop_index('ix_messages_session_created', table_name='messages')
    op.drop_index('ix_reports_user_kind_created', table_name='reports')
    op.drop_index('ix_daily_logs_user_date_desc', table_name='daily_logs')