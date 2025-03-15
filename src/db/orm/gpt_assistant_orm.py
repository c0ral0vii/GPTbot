from decimal import Decimal
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.db.models import GPTAssistant


class GPTAssistantOrm:
    @staticmethod
    async def get_all_assistants(
            session: AsyncSession = None,
    ):
        if session is None:
            session = AsyncSession()

        stmt = select(GPTAssistant).where(
            GPTAssistant.disable == True
        )
        result = await session.execute(stmt)
        gpt_assis = result.scalars().all()

        return gpt_assis if gpt_assis else []

    @staticmethod
    async def create_new_assistant(
            data: Dict[str, Any],
            session: AsyncSession = None,
    ):
        if session is None:
            session = AsyncSession()

        new_asis = GPTAssistant(
            title=data["title"],
            assistant_id=data["assistant_id"],
            premium_free=data.get("premium_free", False),
            comment=data.get("comment", "-"),
            energy_cost=Decimal(data.get("energy_cost", 10)),
            disable=data.get("disable", False),
        )