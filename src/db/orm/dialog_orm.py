from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import async_session
from src.db.enums_class import MessageRole
from src.db.models import Dialog, Message


class DialogORM:
    @staticmethod
    async def get_dialog(dialog_id: int, session: AsyncSession = None):
        if not session:
            session = async_session()

        stmt = select(Dialog).where(Dialog.id == dialog_id)
        result = await session.execute(stmt)
        dialog = result.scalar_one_or_none()
        if not session:
            await session.close()

        return dialog

    @staticmethod
    async def create_dialog(
        user_id: int,
        select_model: str,
        title: str = "Не указан",
        session: AsyncSession = None,
    ) -> Dialog:
        """Создание диалога"""
        if not session:
            session = async_session()

        new_dialog = Dialog(
            user_id=user_id,
            title=title,
            gpt_select=select_model,
        )
        session.add(new_dialog)
        await session.commit()
        await session.refresh(new_dialog)

        if not session:
            await session.close()

        return new_dialog

    @staticmethod
    async def get_dialogs(
        user_id: int, select_model: str, session: AsyncSession = None
    ) -> Optional[List[Dialog]]:
        if not session:
            session = async_session()

        stmt = (
            select(Dialog)
            .where(
                and_(
                    Dialog.user_id == user_id,
                    Dialog.gpt_select == select_model,
                )
            )
            .options(selectinload(Dialog.messages))
        )

        result = await session.execute(stmt)
        dialogs = result.scalars().all()

        dialog_list = [dialog for dialog in dialogs]

        if not session:
            await session.close()

        return dialog_list

    @staticmethod
    async def get_dialog_messages(
        dialog: Dialog | int, session: AsyncSession = None
    ) -> Optional[List[Message]]:
        if not session:
            session = async_session()

        if isinstance(dialog, int):
            stmt = (
                select(Dialog)
                .where(Dialog.id == dialog)
                .options(selectinload(Dialog.messages))
            )
            result = await session.execute(stmt)
            dialog = result.scalar_one_or_none()

        if not dialog:
            return None

        return dialog.messages if dialog.messages else []

    @staticmethod
    async def add_message_to_dialog(
        dialog: Dialog | int,
        role: MessageRole,
        message: str,
        session: AsyncSession = None,
    ) -> bool:
        if not session:
            session = async_session()

        if isinstance(dialog, (str, int)):
            stmt = (
                select(Dialog)
                .where(Dialog.id == int(dialog))
                .options(selectinload(Dialog.messages))
            )
            result = await session.execute(stmt)
            dialog = result.scalar_one_or_none()
            if dialog.title == "Не указан":
                dialog.title = message[:127]

        new_message = Message(
            dialog_id=dialog.id,
            role=role,
            message=message,
        )

        dialog.messages.append(new_message)
        session.add(new_message)
        await session.commit()

        if not session:
            await session.close()

        return True
