"""Add tool_group_id to task_templates table.

Revision ID: add_tool_group_1025
Revises: 522ded944960
Create Date: 2025-10-25 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_tool_group_1025'
down_revision = '522ded944960'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tool_group_id column to task_templates table
    op.add_column('task_templates', sa.Column('tool_group_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f('fk_task_templates_tool_group_id_tool_groups'),
        'task_templates',
        'tool_groups',
        ['tool_group_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop the foreign key and column
    op.drop_constraint(
        op.f('fk_task_templates_tool_group_id_tool_groups'),
        'task_templates',
        type_='foreignkey'
    )
    op.drop_column('task_templates', 'tool_group_id')
