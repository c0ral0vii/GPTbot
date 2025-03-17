from decimal import Decimal
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.db.database import async_session

from src.db.models import GPTAssistant


class GPTAssistantOrm:
    @staticmethod
    async def get_select_assistants(
            assist_id: int,
            session: AsyncSession = None,
    ) -> GPTAssistant:
        """Получить выбраного ассистента"""

        if not session:
            session = async_session()

        stmt = select(GPTAssistant).where(and_(
            GPTAssistant.id == assist_id,
        ))
        result = await session.execute(stmt)
        assists = result.scalars().first()

        if not session:
            await session.close()

        return assists

    @staticmethod
    async def get_all_assistants(
            session: AsyncSession = None,
    ) -> List[GPTAssistant]:
        if session is None:
            session = async_session()

        stmt = select(GPTAssistant)
        result = await session.execute(stmt)
        gpt_assis = result.scalars().all()

        if not session:
            await session.close()

        return gpt_assis if gpt_assis else []

    @staticmethod
    async def create_new_assistant(
            data: Dict[str, Any],
            session: AsyncSession = None,
    ) -> None:
        try:
            if session is None:
                session = async_session()

            new_asis = GPTAssistant(
                title=data["title"],
                assistant_id=data["assistant_id"],
                premium_free=data.get("premium_free", False),
                comment=data.get("comment", "-"),
                energy_cost=Decimal(data.get("energy_cost", 10)),
                disable=data.get("disable", False),
            )

            session.add(new_asis)
            await session.commit()

            if not session:
                await session.close()
        except Exception as e:
            await session.rollback()
            await session.close()

    @staticmethod
    async def update_assistant(
            data: Dict[str, Any],
            session: AsyncSession = None,
    ) -> None:
        if session is None:
            session = async_session()

        stmt = select(GPTAssistant).where(GPTAssistant.id == data["id"])
        result = await session.execute(stmt)
        gpt_assis = result.scalars().first()

        gpt_assis.title = data["title"]
        gpt_assis.assistant_id = data["assistant_id"]
        gpt_assis.premium_free = data.get("premium_free", False)
        gpt_assis.comment = data.get("comment", "-")
        gpt_assis.energy_cost = Decimal(data.get("energy_cost", 10))
        gpt_assis.disable = data.get("disable", False)

        await session.commit()
        if not session:
            await session.close()

    @staticmethod
    async def delete_assistant(
            data: Dict[str, Any],
            session: AsyncSession = None,
    ) -> None:
        if session is None:
            session = async_session()

        stmt = select(GPTAssistant).where(GPTAssistant.id == data["id"])
        result = await session.execute(stmt)
        gpt_assis = result.scalars().first()

        await session.delete(gpt_assis)
        await session.commit()

        if not session:
            await session.close()