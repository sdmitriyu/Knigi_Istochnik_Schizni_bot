from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Hello, world!")

@router.message(Command("help"))
async def help(message: Message):
    await message.answer("Help")


