from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.enums_class import MessageRole
from src.db.models import Dialog, Message
from src.db.custom_decorators import with_session


class DialogORM:
    @staticmethod
    @with_session
    async def get_dialog(
        dialog_id: int, session: AsyncSession = None
    ) -> Optional[Dialog]:
        """Получить диалог по ID"""
        stmt = select(Dialog).where(Dialog.id == dialog_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    @with_session
    async def create_dialog(
        user_id: int,
        select_model: str,
        title: str = "Не указан",
        session: AsyncSession = None,
    ) -> Dialog:
        """Создание нового диалога"""
        new_dialog = Dialog(
            user_id=user_id,
            title=title,
            gpt_select=select_model,
        )
        session.add(new_dialog)
        await session.commit()
        await session.refresh(new_dialog)
        return new_dialog

    @staticmethod
    @with_session
    async def get_dialogs(
        user_id: int, select_model: str, session: AsyncSession = None
    ) -> List[Dialog]:
        """Получить все диалоги пользователя"""
        stmt = (
            select(Dialog)
            .where(and_(Dialog.user_id == user_id, Dialog.gpt_select == select_model))
            .options(selectinload(Dialog.messages))
            .order_by(Dialog.id.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().all() or []

    @staticmethod
    @with_session
    async def get_dialog_messages(
        dialog: Dialog | int, session: AsyncSession = None, limit: int = 32
    ) -> List[Message]:
        """Получить последние сообщения в диалоге (по умолчанию 32)"""

        if isinstance(dialog, int):
            stmt = select(Dialog).where(Dialog.id == dialog)
            result = await session.execute(stmt)
            dialog = result.scalar_one_or_none()
            if not dialog:
                return []

        stmt = (
            select(Message)
            .where(Message.dialog_id == dialog.id)
            .order_by(Message.message_id.asc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        messages = list(result.scalars().all())
        return messages

    @staticmethod
    @with_session
    async def get_dialog_messages_by_uuid(
        uuid: str, session: AsyncSession = None, limit: int = 32
    ) -> List[Message]:
        """Получить последние сообщения в диалоге по UUID (по умолчанию 32)"""
        
        # Сначала получаем сам диалог, чтобы узнать заголовок и дату создания
        dialog_stmt = (
            select(Dialog)
            .where(Dialog.uuid == uuid)
        )
        
        dialog_result = await session.execute(dialog_stmt)
        dialog = dialog_result.scalar_one_or_none()
        
        if not dialog:
            return {}
        
        # Затем получаем сообщения
        stmt = (
            select(Message)
            .where(Message.dialog_id == dialog.id)
            .order_by(Message.message_id.asc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        messages = list(result.scalars().all())
        
        if not messages:
            # Если сообщений нет, всё равно возвращаем информацию о диалоге
            return {
                "title": dialog.title,
                "gpt_select": dialog.gpt_select,
                "created_at": dialog.created.isoformat(),
                "messages": []
            }
        
        # Формируем список сообщений
        messages_list = []
        for msg in messages:
            messages_list.append({
                "role": msg.role.value,
                "message": msg.message,
                "message_id": msg.message_id
            })
        
        # Возвращаем полные данные о диалоге
        return {
            "title": dialog.title,
            "gpt_select": dialog.gpt_select,
            "created_at": dialog.created.isoformat(),
            "messages": messages_list
        }
    
    @staticmethod
    @with_session
    async def add_message_to_dialog(
        dialog: Dialog | int,
        role: MessageRole,
        message: str,
        session: AsyncSession = None,
    ) -> bool:
        """Добавить сообщение в диалог"""
        if isinstance(dialog, (str, int)):
            stmt = (
                select(Dialog)
                .where(Dialog.id == int(dialog))
                .options(selectinload(Dialog.messages))
            )
            result = await session.execute(stmt)
            dialog = result.scalar_one_or_none()

        if not dialog:
            return False  # Диалог не найден

        if dialog.title == "Не указан":
            dialog.title = message[:127]

        new_message = Message(dialog_id=dialog.id, role=role, message=message)
        session.add(new_message)
        await session.commit()

        return True

    @staticmethod
    @with_session
    async def update_dialog(dialog_id: int, title: str, session: AsyncSession = None):
        """Обновить название диалога"""
        stmt = select(Dialog).where(Dialog.id == dialog_id)
        result = await session.execute(stmt)
        dialog = result.scalar_one_or_none()
        if dialog:
            dialog.title = title
            await session.commit()
            await session.refresh(dialog)

        return dialog

    @staticmethod
    @with_session
    async def delete_dialog(dialog_id: int, session: AsyncSession = None):
        """Удалить диалог"""

        stmt = select(Dialog).where(Dialog.id == dialog_id)
        result = await session.execute(stmt)
        dialog = result.scalar_one_or_none()
        if dialog:
            await session.delete(dialog)
            await session.commit()
            return True
        return False
