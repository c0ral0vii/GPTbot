"""change claude version

Revision ID: 9227dafbfc23
Revises: 8be029dc499a
Create Date: 2025-04-07 12:56:08.324194

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9227dafbfc23"
down_revision: Union[str, None] = "8be029dc499a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    
    op.execute(
        "UPDATE user_config SET claude_select = 'CLAUDE_VERSION_SONNET' "
        "WHERE claude_select = 'CLAUDE_VERSION_HAIKU'"
    )
    
    # Создаем временный тип enum с новыми значениями
    new_enum = sa.Enum(
        "CLAUDE_VERSION_SONNET",
        "CLAUDE_VERSION_SONNET37",
        name="claudeconfig_new"
    )
    new_enum.create(op.get_bind(), checkfirst=True)
    
    # Изменяем тип столбца на временный enum
    op.alter_column(
        "user_config",
        "claude_select",
        type_=new_enum,
        postgresql_using="claude_select::text::claudeconfig_new"
    )
    
    # Удаляем старый enum
    op.execute("DROP TYPE claudeconfig")
    
    # Переименовываем временный enum в оригинальное имя
    op.execute("ALTER TYPE claudeconfig_new RENAME TO claudeconfig")

    op.execute("UPDATE dialogs SET gpt_select = 'claude-3-5-sonnet-20241022'"
               "WHERE gpt_select = 'claude-3-5-haiku-latest'")
    op.execute("UPDATE dialogs SET gpt_select = 'claude-3-5-sonnet-20241022'"
               "WHERE gpt_select = 'claude-3-5-sonnet-latest'")

def downgrade():
    # Создаем временный enum со старыми значениями
    old_enum = sa.Enum(
        "CLAUDE_VERSION_SONNET",
        "CLAUDE_VERSION_HAIKU",
        name="claudeconfig_old"
    )
    old_enum.create(op.get_bind(), checkfirst=True)
    
    # Изменяем тип столбца на временный enum
    op.alter_column(
        "user_config",
        "claude_select",
        type_=old_enum,
        postgresql_using="CASE "
                         "WHEN claude_select = 'CLAUDE_VERSION_SONNET' THEN 'CLAUDE_VERSION_SONNET'::claudeconfig_old "
                         "ELSE 'CLAUDE_VERSION_SONNET'::claudeconfig_old "
                         "END"
    )
    
    # Удаляем новый enum
    op.execute("DROP TYPE claudeconfig")
    
    # Переименовываем временный enum в оригинальное имя
    op.execute("ALTER TYPE claudeconfig_old RENAME TO claudeconfig")