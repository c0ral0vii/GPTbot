"""change coun string in message

Revision ID: a37d0402b4ef
Revises: 749b7c5b6adb
Create Date: 2025-03-27 03:33:46.627566

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a37d0402b4ef"
down_revision: Union[str, None] = "749b7c5b6adb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "messages",
        "message",
        existing_type=sa.VARCHAR(length=20000),
        type_=sa.String(length=25000),
        existing_nullable=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "messages",
        "message",
        existing_type=sa.String(length=25000),
        type_=sa.VARCHAR(length=20000),
        existing_nullable=False,
    )
    # ### end Alembic commands ###
