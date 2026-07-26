"""initial schema

Revision ID: b373f82cb618
Revises:
Create Date: 2020-04-17 12:08:56.331161

"""

from alembic import op
import sqlalchemy as sa


revision = 'b373f82cb618'
down_revision = None
branch_labels = None
depends_on = None


def _has_column(inspector, table_name, column_name):
    return any(column['name'] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector, table_name, index_name):
    return any(index['name'] == index_name for index in inspector.get_indexes(table_name))


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('room'):
        op.create_table(
            'room',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=4), nullable=False),
            sa.Column('game', sa.String(length=32), nullable=False),
            sa.Column('state', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
        )
    else:
        with op.batch_alter_table('room') as batch_op:
            if not _has_column(inspector, 'room', 'game'):
                batch_op.add_column(sa.Column('game', sa.String(length=32), nullable=False, server_default='ghost'))
            if not _has_column(inspector, 'room', 'state'):
                batch_op.add_column(sa.Column('state', sa.Text(), nullable=False, server_default='{}'))
            if not _has_column(inspector, 'room', 'created_at'):
                batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=False, server_default='1970-01-01 00:00:00'))

    if inspector.has_table('user') and not inspector.has_table('player'):
        op.rename_table('user', 'player')

    inspector = sa.inspect(bind)

    if not inspector.has_table('player'):
        op.create_table(
            'player',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('token', sa.String(length=64), nullable=False),
            sa.Column('room_name', sa.String(length=4), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['room_name'], ['room.name']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('token'),
        )
    else:
        with op.batch_alter_table('player') as batch_op:
            if _has_column(inspector, 'player', 'sid') and not _has_column(inspector, 'player', 'token'):
                batch_op.alter_column('sid', new_column_name='token')
            if not _has_column(inspector, 'player', 'created_at'):
                batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=False, server_default='1970-01-01 00:00:00'))

    inspector = sa.inspect(bind)
    if not _has_index(inspector, 'player', 'ix_player_token'):
        op.create_index(op.f('ix_player_token'), 'player', ['token'], unique=False)

    if not inspector.has_table('room_event'):
        op.create_table(
            'room_event',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('room_name', sa.String(length=4), nullable=False),
            sa.Column('event_type', sa.String(length=64), nullable=False),
            sa.Column('payload', sa.Text(), nullable=False),
            sa.Column('recipient_token', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['room_name'], ['room.name']),
            sa.PrimaryKeyConstraint('id'),
        )

    inspector = sa.inspect(bind)
    if not _has_index(inspector, 'room_event', 'ix_room_event_recipient_token'):
        op.create_index(op.f('ix_room_event_recipient_token'), 'room_event', ['recipient_token'], unique=False)
    if not _has_index(inspector, 'room_event', 'ix_room_event_room_name'):
        op.create_index(op.f('ix_room_event_room_name'), 'room_event', ['room_name'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('room_event'):
        if _has_index(inspector, 'room_event', 'ix_room_event_room_name'):
            op.drop_index(op.f('ix_room_event_room_name'), table_name='room_event')
        if _has_index(inspector, 'room_event', 'ix_room_event_recipient_token'):
            op.drop_index(op.f('ix_room_event_recipient_token'), table_name='room_event')
        op.drop_table('room_event')

    inspector = sa.inspect(bind)
    if inspector.has_table('player'):
        if _has_index(inspector, 'player', 'ix_player_token'):
            op.drop_index(op.f('ix_player_token'), table_name='player')
        op.drop_table('player')

    inspector = sa.inspect(bind)
    if inspector.has_table('room'):
        op.drop_table('room')
