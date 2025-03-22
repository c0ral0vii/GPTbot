from decimal import Decimal
from typing import Dict, Any, List, Optional, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import BonusLink
from src.db.custom_decorators import with_session


class BonusLinksOrm:
    @staticmethod
    @with_session
    async def create_bonus_links(
        data: Dict[str, Any],
        session: AsyncSession = None,
    ):
        new_bonus_link = BonusLink(
            energy_bonus=Decimal(data["energy_bonus"]),
            link=data["link"],
            active=data.get("active", True),
            active_count=data.get("active_count", 0),
        )
        session.add(new_bonus_link)
        await session.commit()

    @staticmethod
    @with_session
    async def get_all_bonuses(
        session: AsyncSession = None,
    ) -> List[BonusLink]:
        stmt = select(BonusLink)
        result = await session.execute(stmt)
        bonuses_links = result.scalars().all()

        return bonuses_links if bonuses_links else []

    @staticmethod
    @with_session
    async def update_bonus_link(
        data: Dict[str, Any],
        session: AsyncSession = None,
    ) -> None:
        stmt = select(BonusLink).where(BonusLink.id == data["id"])
        result = await session.execute(stmt)
        bonus_link = result.scalar_one_or_none()

        if not bonus_link:
            return

        bonus_link.energy_bonus = Decimal(data["energy_bonus"])
        bonus_link.link = data["link"]
        bonus_link.active = data["active"]
        bonus_link.active_count = data["active_count"]

        await session.commit()

    @staticmethod
    @with_session
    async def get_bonus_link(
        link_id: int = None,
        link: str = None,
        session: AsyncSession = None,
    ) -> Optional[BonusLink]:
        if link:
            stmt = select(BonusLink).where(BonusLink.link == link)
        elif link_id:
            stmt = select(BonusLink).where(BonusLink.id == link_id)
        if not link_id and not link:
            return None

        result = await session.execute(stmt)
        bonus_link = result.scalar_one_or_none()

        if bonus_link is None:
            return None

        return bonus_link

    @staticmethod
    @with_session
    async def use_bonus_link(
        link: str,
        operation: Literal["remove", "add"] = "remove",
        session: AsyncSession = None,
    ) -> Optional[BonusLink]:
        stmt = select(BonusLink).where(BonusLink.link == link)
        result = await session.execute(stmt)
        bonus_link = result.scalar_one_or_none()

        if bonus_link is None:
            return None

        use_count = bonus_link.active_count if bonus_link else 0

        if use_count <= 0:
            bonus_link.active = False
            await session.commit()
            return None

        if operation == "remove":
            bonus_link.active_count = use_count - 1

        if operation == "add":
            bonus_link.active_count = use_count + 1

        await session.commit()
        return bonus_link
