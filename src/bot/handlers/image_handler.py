from aiogram import Router, types, F
from click import Command

router = Router()


@router.message(Command("image"))
async def handle_image(message: types.Message):
    await message.answer("В разработке!")