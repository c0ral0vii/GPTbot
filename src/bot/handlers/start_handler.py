from aiogram import Router, types, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.main_menu import main_menu_kb
from src.db.orm.user_orm import UserORM
from src.utils.logger import setup_logger
from src.scripts.queue.rabbit_queue import model


router = Router()
logger = setup_logger(__name__)

@router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    try:
        logger.debug(message.text)
        if message.text.find("="):
            referral_link = message.text.split(" ")
            if referral_link[-1] != "/start":
                user = await UserORM.create_user(message.from_user.id, referral_link[-1])

                if not user.get("duplicate"):
                    owner = await UserORM.get_owner_referral(referral_link[-1])

                    if owner:
                        await model.publish_message(
                            queue_name="referral",
                            user_id=owner.get("user_id"),
                            text="❗ У вас новый рефералл, вы получили +20 ⚡ энергии.",
                        )
                        await UserORM.add_energy(message.from_user.id, 20)
            else:
                await UserORM.create_user(message.from_user.id)

        else:
            await UserORM.create_user(message.from_user.id)


        await message.answer(
            "Выберите нейросеть:\n\n"
            "*🤖 Чат-ассистенты::*\n\n"
            "• /text — Работа с текстом. \n"
            "• /image — Работа с изображениями. \n"
            "• /code — Работа с кодом. \n"
            "\n*⚙️ Управление:* \n\n"
            "• /profile — Баланс генераций \n"
            "• /invite — Пригласить друга (+20💎 генераций) \n"
            "• /bonus — Бесплатный нейро-курс (до +70💎 генераций) \n"
            "• /premium — 🌟 Premium подписка (1000💎 генераций) \n\n"
            "/start — Сменить нейросеть",
            parse_mode="Markdown",
            reply_markup=await main_menu_kb(),
        )

        await state.clear()
    except Exception as e:
        logger.error(e)
        await message.answer("Произошла ошибка, попробуйте еще раз")


@router.message(Command("invite"))
async def invite_handler(message: types.Message, state: FSMContext, bot: Bot):
    try:
        referral_link = await UserORM.get_referral_link(message.from_user.id)
        await message.answer(
            f"Регистрируйся по ссылке и получишь +20 ⚡ бесплатной энергии:\n"
            f"https://t.me/galsfhdjkjas_bot?start={referral_link}",
        )

    except Exception as e:
        logger.error(e)
        await message.answer("Попробуйте прописать команду /start")