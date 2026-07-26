"""expand room name columns

Revision ID: 8d2b6d9b4f11
Revises: b373f82cb618
Create Date: 2026-07-26 18:25:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "8d2b6d9b4f11"
down_revision = "b373f82cb618"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("room") as batch_op:
        batch_op.alter_column("name", existing_type=sa.String(length=4), type_=sa.String(length=64))

    with op.batch_alter_table("player") as batch_op:
        batch_op.alter_column("room_name", existing_type=sa.String(length=4), type_=sa.String(length=64))

    with op.batch_alter_table("room_event") as batch_op:
        batch_op.alter_column("room_name", existing_type=sa.String(length=4), type_=sa.String(length=64))


def downgrade():
    with op.batch_alter_table("room_event") as batch_op:
        batch_op.alter_column("room_name", existing_type=sa.String(length=64), type_=sa.String(length=4))

    with op.batch_alter_table("player") as batch_op:
        batch_op.alter_column("room_name", existing_type=sa.String(length=64), type_=sa.String(length=4))

    with op.batch_alter_table("room") as batch_op:
        batch_op.alter_column("name", existing_type=sa.String(length=64), type_=sa.String(length=4))
