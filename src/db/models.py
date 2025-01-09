from sqlalchemy import (
    func,
    String,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Text,
    Boolean,
    Numeric,
    Table,
    Column,
    Date,
    select,
)

from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(BigInteger, nullable=False, unique=True)

    use_count: Mapped[int] = Column(BigInteger, nullable=True)


class PremiumUser(Base):
    __tablename__ = "premium_users"

    id: Mapped[int] = Column(Integer, primary_key=True)
    user: Mapped["User"] = ForeignKey("users.id")

    premium_active: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_to_date: Mapped[Date] = mapped_column(Date, default=False)
