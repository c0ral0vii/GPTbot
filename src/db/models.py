from decimal import Decimal
from typing import List

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

from src.db.enums_class import (
    MessageRole,
    GPTConfig,
    CLAUDEConfig,
    MidjourneySpeedConfig,
)


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(nullable=True)

    energy: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 1), nullable=False, default=Decimal("100")
    )

    use_referral_link: Mapped[int] = mapped_column(BigInteger, nullable=True)
    personal_percent: Mapped[int] = mapped_column(Integer, default=13)
    referral_bonus: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 1), nullable=False, default=Decimal("0")
    )

    premium_status: Mapped["PremiumUser"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    dialogs: Mapped[list["Dialog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    user_config_model: Mapped["UserConfig"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserConfig(Base):
    __tablename__ = "user_config"

    gpt_select: Mapped[GPTConfig] = mapped_column(
        SQLEnum(GPTConfig), default=GPTConfig.GPT_VERSION_4o_mini
    )
    claude_select: Mapped[CLAUDEConfig] = mapped_column(
        SQLEnum(CLAUDEConfig), default=CLAUDEConfig.CLAUDE_VERSION_SONNET
    )
    midjourney_speed: Mapped[MidjourneySpeedConfig] = mapped_column(
        SQLEnum(MidjourneySpeedConfig), default=MidjourneySpeedConfig.RELAX
    )

    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=False)

    user_id: Mapped["User"] = mapped_column(
        ForeignKey("users.user_id"), primary_key=True
    )
    user: Mapped["User"] = relationship("User", back_populates="user_config_model")


class PremiumUser(Base):
    __tablename__ = "premium_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    premium_active: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_from_date: Mapped[Date] = mapped_column(Date, default=False)
    premium_to_date: Mapped[Date] = mapped_column(Date, default=False)

    auth_renewal_id: Mapped[str] = mapped_column(nullable=True)
    last_pay_count: Mapped[int] = mapped_column(nullable=True, default=1500)

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


class Dialog(Base):
    __tablename__ = "dialogs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_id: Mapped["User"] = mapped_column(ForeignKey("users.user_id"))
    user: Mapped["User"] = relationship("User", back_populates="dialogs")

    title: Mapped[str] = mapped_column(String(128), nullable=False)

    gpt_select: Mapped[str] = mapped_column(nullable=False)
    messages: Mapped[List["Message"]] = relationship(
        back_populates="dialog", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    dialog_id: Mapped[int] = mapped_column(ForeignKey("dialogs.id"), primary_key=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole), nullable=False)
    message: Mapped[str] = mapped_column(String(25000), nullable=False)

    dialog: Mapped["Dialog"] = relationship(back_populates="messages")


class BonusLink(Base):
    __tablename__ = "bonus_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    energy_bonus: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 1), nullable=False, default=Decimal("10")
    )
    link: Mapped[str] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(default=True)
    active_count: Mapped[int] = mapped_column(default=0)


class PaymentPromocode(Base):
    __tablename__ = "payment_promocodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    discount: Mapped[int] = mapped_column()

    enable: Mapped[bool] = mapped_column(default=True)
    count_active: Mapped[int] = mapped_column(default=0)


class GPTAssistant(Base):
    __tablename__ = "gpt_assistants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(nullable=True)
    assistant_id: Mapped[str] = mapped_column(unique=True)
    premium_free: Mapped[bool] = mapped_column(default=False)
    only_for_premium: Mapped[bool] = mapped_column(default=True, nullable=True)

    comment: Mapped[str] = mapped_column(nullable=True)

    energy_cost: Mapped[Decimal] = mapped_column(DECIMAL(15, 1), nullable=False)
    disable: Mapped[bool] = mapped_column(default=False)
