"""finish

Revision ID: bb3f8adee1c9
Revises: 
Create Date: 2025-03-13 03:37:12.250042

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bb3f8adee1c9"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "banned_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "bonus_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("energy_bonus", sa.DECIMAL(precision=15, scale=1), nullable=False),
        sa.Column("link", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("active_count", sa.Integer(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "generate_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("image_name", sa.String(), nullable=True),
        sa.Column("prompt", sa.String(), nullable=True),
        sa.Column("hash", sa.String(), nullable=False),
        sa.Column("first_hash", sa.String(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("energy", sa.DECIMAL(precision=15, scale=1), nullable=False),
        sa.Column("use_referral_link", sa.BigInteger(), nullable=True),
        sa.Column("personal_percent", sa.Integer(), nullable=False),
        sa.Column("referral_bonus", sa.DECIMAL(precision=15, scale=1), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "dialogs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("gpt_select", sa.String(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "premium_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("premium_active", sa.Boolean(), nullable=False),
        sa.Column("premium_from_date", sa.Date(), nullable=False),
        sa.Column("premium_to_date", sa.Date(), nullable=False),
        sa.Column("auth_renewal_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_config",
        sa.Column(
            "gpt_select",
            sa.Enum(
                "GPT_VERSION_4o",
                "GPT_VERSION_4o_mini",
                "GPT_VERSION_o1",
                "GPT_VERSION_45",
                name="gptconfig",
            ),
            nullable=False,
        ),
        sa.Column(
            "claude_select",
            sa.Enum(
                "CLAUDE_VERSION_SONNET",
                "CLAUDE_VERSION_HAIKU",
                name="claudeconfig",
            ),
            nullable=False,
        ),
        sa.Column("auto_renewal", sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "messages",
        sa.Column("dialog_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "role",
            sa.Enum("USER", "ASSISTANT", name="messagerole"),
            nullable=False,
        ),
        sa.Column("message", sa.String(length=5000), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dialog_id"],
            ["dialogs.id"],
        ),
        sa.PrimaryKeyConstraint("dialog_id", "message_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("messages")
    op.drop_table("user_config")
    op.drop_table("premium_users")
    op.drop_table("dialogs")
    op.drop_table("users")
    op.drop_table("generate_images")
    op.drop_table("bonus_links")
    op.drop_table("banned_users")
    # ### end Alembic commands ###
