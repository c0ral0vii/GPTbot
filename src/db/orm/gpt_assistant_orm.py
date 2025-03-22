from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models import GPTAssistant
from src.db.custom_decorators import with_session


class GPTAssistantOrm:
    @staticmethod
    @with_session
    async def get_select_assistants(
        assist_id: int,
        session: AsyncSession = None,
    ) -> GPTAssistant | None:
        """Получить выбранного ассистента"""
        stmt = select(GPTAssistant).where(GPTAssistant.id == assist_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    @with_session
    async def get_all_assistants(
        session: AsyncSession = None,
    ) -> List[GPTAssistant]:
        """Получить всех ассистентов"""
        stmt = select(GPTAssistant)
        result = await session.execute(stmt)
        return result.scalars().all() or []

    @staticmethod
    @with_session
    async def create_new_assistant(
        data: Dict[str, Any],
        session: AsyncSession = None,
    ) -> None:
        """Создать нового ассистента"""
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

    @staticmethod
    @with_session
    async def update_assistant(
        data: Dict[str, Any],
        session: AsyncSession = None,
    ) -> None:
        """Обновить ассистента"""
        stmt = select(GPTAssistant).where(GPTAssistant.id == data["id"])
        result = await session.execute(stmt)
        gpt_assis = result.scalars().first()

        if gpt_assis is None:
            raise ValueError(f"Assistant with id {data['id']} not found")

        gpt_assis.title = data["title"]
        gpt_assis.assistant_id = data["assistant_id"]
        gpt_assis.premium_free = data.get("premium_free", False)
        gpt_assis.comment = data.get("comment", "-")
        gpt_assis.energy_cost = Decimal(data.get("energy_cost", 10))
        gpt_assis.disable = data.get("disable", False)

        await session.commit()

    @staticmethod
    @with_session
    async def delete_assistant(
        data: Dict[str, Any],
        session: AsyncSession = None,
    ) -> None:
        """Удалить ассистента"""
        stmt = select(GPTAssistant).where(GPTAssistant.id == data["id"])
        result = await session.execute(stmt)
        gpt_assis = result.scalars().first()

        if gpt_assis is None:
            raise ValueError(f"Assistant with id {data['id']} not found")

        await session.delete(gpt_assis)
        await session.commit()
