from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F, Router

router = Router()


@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(f"Hello, {message.from_user.full_name}!")
