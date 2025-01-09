from aiogram import Router, types, F
from aiogram.filters import Command


router = Router()


@router.message(Command("code"))
async def code_handler(message: types.Message):
    await message.answer("В разработке!")
