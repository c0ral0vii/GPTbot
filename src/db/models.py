from decimal import Decimal

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
    Date,
    select,
    DECIMAL,
)

from sqlalchemy.orm import Mapped, DeclarativeBase, relationship, mapped_column


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)

    energy: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 1), nullable=True, default=Decimal("10")
    )

    referral_link: Mapped[str] = mapped_column(nullable=True)
    use_referral_link: Mapped[str] = mapped_column(nullable=True)

    premium_status: Mapped["PremiumUser"] = relationship(back_populates="user")


class PremiumUser(Base):
    __tablename__ = "premium_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    premium_active: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_to_date: Mapped[Date] = mapped_column(Date, default=False)

    user_id: Mapped["User"] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="premium_status")


class BannedUser(Base):
    __tablename__ = "banned_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
