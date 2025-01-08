import asyncio

from aiogram import Bot, Dispatcher, types

from src.config.config import settings
from src.utils.logger import setup_logger
from src.bot.handlers import (
    cancel_handler,
    start_handler,

    code_handler,
    image_handler,
    text_handler,
)

bot = Bot(token=settings.bot_api)
dp = Dispatcher()
logger = setup_logger(__name__)

dp.include_routers(
    cancel_handler.router,
    start_handler.router,

    code_handler.router,
    image_handler.router,
    text_handler.router,
)

async def on_startup():
    logger.info("Инициализация комманд")

    commands = [
        types.BotCommand(command="/start", description="Перезапуск бота (Restart bot)"),
        types.BotCommand(command="/text", description="Работа с текстовыми ИИ"),
        types.BotCommand(command="/image", description="Работа с ИИ для изображений"),
        types.BotCommand(command="/code", description="Работа с ИИ для кода"),
    ]

    await bot.set_my_commands(commands)


async def run():
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup()
    logger.info("Запуск бота")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())