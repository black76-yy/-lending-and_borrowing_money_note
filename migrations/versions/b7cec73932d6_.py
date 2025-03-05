"""empty message

Revision ID: b7cec73932d6
Revises: a8d81ec06661
Create Date: 2024-08-11 16:10:15.557719

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7cec73932d6'
down_revision = 'a8d81ec06661'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('return_money',
    sa.Column('return_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('party_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['party_id'], ['party.party_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
    sa.PrimaryKeyConstraint('return_id')
    )
    op.create_table('returned_money',
    sa.Column('returned_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('party_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['party_id'], ['party.party_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
    sa.PrimaryKeyConstraint('returned_id')
    )
    with op.batch_alter_table('party', schema=None) as batch_op:
        batch_op.drop_column('returned_money')
        batch_op.drop_column('return_money')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('party', schema=None) as batch_op:
        batch_op.add_column(sa.Column('return_money', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('returned_money', sa.INTEGER(), nullable=True))

    op.drop_table('returned_money')
    op.drop_table('return_money')
    # ### end Alembic commands ###
