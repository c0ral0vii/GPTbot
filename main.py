import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.redis import RedisStorage as redis_storage


from src.scripts.queue.worker import QueueWorker
from src.utils.redis_cache.redis_cache import redis_manager
from src.config.config import settings
from src.utils.logger import setup_logger
from src.bot.handlers import (
    cancel_handler,
    dialogs_config_handler,
    start_handler,
    image_handler,
    text_handler,
    profile_handler,
    premium_handler,
    assist_handler,
)

from src.bot.middlewares.antiflood import RateLimitMiddleware
from src.bot.filters.chat_type import ChatTypeFilter
from src.bot.middlewares.banned import BlockMiddleware

bot = Bot(token=settings.BOT_API)
dp = Dispatcher(storage=redis_storage(redis=redis_manager.get_redis_manager()))

dp.message.middleware(BlockMiddleware())
dp.message.middleware(RateLimitMiddleware())
dp.message.filter(ChatTypeFilter(["private"]))

logger = setup_logger(__name__)

dp.include_routers(
    cancel_handler.router,
    start_handler.router,
    premium_handler.router,
    profile_handler.router,
    image_handler.router,
    text_handler.router,
    assist_handler.router,
    dialogs_config_handler.router,
)


async def on_startup():
    logger.info("Инициализация комманд")

    commands = [
        types.BotCommand(command="/start", description="Перезапуск бота (Restart bot)"),
        types.BotCommand(command="/menu", description="Меню бота"),
        types.BotCommand(command="/pro", description="🌟 PRO подписка"),
        types.BotCommand(command="/text", description="Работа с текстовыми ИИ"),
        types.BotCommand(command="/image", description="Работа с ИИ для изображений"),
        types.BotCommand(
            command="/assistants", description="Работа с нашими Ассистентами"
        ),
        types.BotCommand(command="/profile", description="Баланс генераций"),
        types.BotCommand(command="/invite", description="Пригласить друга"),
        types.BotCommand(command="/help", description="Поддержка"),
        types.BotCommand(command="/subscription", description="Управление подпиской"),
    ]

    await bot.set_my_commands(commands)


async def run():
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup()

    logger.info("Запуск воркера")

    await run_workers()

    logger.info("Запуск бота")

    await dp.start_polling(bot)
    logger.info("Запуск бота")


async def run_workers():
    worker = QueueWorker()
    task = asyncio.create_task(worker.start())
    await task


if __name__ == "__main__":
    asyncio.run(run())
