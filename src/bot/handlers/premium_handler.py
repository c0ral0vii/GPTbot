from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils.generate_payment import generate_payment
from src.utils.logger import setup_logger

router = Router()
logger = setup_logger(__name__)
PRIVACY_POLICY = "https://gradov.online/ofertaneurokesh"


@router.message(Command("premium"))
async def premium_handle(message: types.Message):
    await message.answer(
        "Стоимость премиума 990 рублей за 1 месяц использования\n"
        f"Перед покупкой ознакомтесь с <a href='{PRIVACY_POLICY}'>политикой конфиденциальности</a>\n\n"
        "После ознакомления нажмите кнопку 'Продолжить' для покупки, нажатием на кнопку вы подтверждаете свою ознакомленость нашей политикой конфиденциальности",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Продолжить", callback_data="continue_premium"
                    )
                ]
            ]
        ),
    )


@router.callback_query(F.data == "continue_premium")
async def buy_premium_link(callback: types.CallbackQuery):
    payment_link = await generate_payment(callback.from_user.id)

    await callback.message.answer(
        "Для покупки перейдите по ссылке снизу",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Оплатить", url=payment_link)],
            ]
        ),
    )
