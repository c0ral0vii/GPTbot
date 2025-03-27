from src.db.enums_class import MessageRole
from src.db.models import Message
from src.db.orm.dialog_orm import DialogORM


class DialogService:
    async def add_message(self, role: MessageRole, dialog_id: int, message: str):
        """Добавление сообщения в диалог"""

        await DialogORM.add_message_to_dialog(
            dialog_id,
            role,
            message[:25000],
        )

    async def get_messages(self, dialog_id) -> list[Message]:
        """Получение сообщений из диалога"""

        messages = await DialogORM.get_dialog_messages(dialog_id)
        return messages
