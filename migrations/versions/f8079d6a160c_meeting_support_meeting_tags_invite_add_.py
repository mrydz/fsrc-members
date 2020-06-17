"""meeting support - meeting: tags; invite: add invitekey, attended, activeinvite

Revision ID: f8079d6a160c
Revises: 28d6724efeb8
Create Date: 2020-06-05 15:04:10.620625

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8079d6a160c'
down_revision = '28d6724efeb8'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('meeting_tag',
    sa.Column('meeting_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['meeting_id'], ['meeting.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], )
    )
    op.add_column('invite', sa.Column('activeinvite', sa.Boolean(), nullable=True))
    op.add_column('invite', sa.Column('attended', sa.Boolean(), nullable=True))
    op.add_column('invite', sa.Column('invitekey', sa.String(length=16), nullable=True))
    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('invite', 'invitekey')
    op.drop_column('invite', 'attended')
    op.drop_column('invite', 'activeinvite')
    op.drop_table('meeting_tag')
    # ### end Alembic commands ###


def upgrade_users():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_users():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###

