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

    energy: Mapped[int] = Column(Integer, nullable=True)
    referal_link: Mapped[str] = Column(Text(255), nullable=True)

    referral_stats: Mapped["ReferralStats"] = relationship(back_populates="user")

    premium_status: Mapped["PremiumUser"] = relationship(back_populates="user")

class ReferralStats(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped["User"] = ForeignKey("users.id")

    referrals: Mapped[list["User"]] = relationship()


class PremiumUser(Base):
    __tablename__ = "premium_users"

    id: Mapped[int] = Column(Integer, primary_key=True)
    user: Mapped["User"] = ForeignKey("users.id")

    premium_active: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_to_date: Mapped[Date] = mapped_column(Date, default=False)


class BannedUser(Base):
    __tablename__ = "banned_users"

    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(BigInteger, nullable=False, unique=True)

