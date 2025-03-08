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
        DECIMAL(15, 1), nullable=False, default=Decimal("10")
    )

    referral_link: Mapped[str] = mapped_column(nullable=True)
    use_referral_link: Mapped[str] = mapped_column(nullable=True)

    premium_status: Mapped["PremiumUser"] = relationship(back_populates="user")


class PremiumUser(Base):
    __tablename__ = "premium_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    premium_active: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_from_date: Mapped[Date] = mapped_column(Date, default=False)
    premium_to_date: Mapped[Date] = mapped_column(Date, default=False)

    user_id: Mapped["User"] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="premium_status")


class BannedUser(Base):
    __tablename__ = "banned_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)


class GenerateImage(Base):
    __tablename__ = "generate_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    image_name: Mapped[str] = mapped_column(nullable=True)
    prompt: Mapped[str] = mapped_column(nullable=True)
    hash: Mapped[str] = mapped_column(nullable=False)
    first_hash: Mapped[str] = mapped_column(nullable=False)


class BonusLink(Base):
    __tablename__ = "bonus_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    energy_bonus: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 1), nullable=False, default=Decimal("10")
    )
    link: Mapped[str] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(default=True)
    active_count: Mapped[int] = mapped_column(default=0)
