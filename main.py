import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, BotCommand, BotCommandScopeAllPrivateChats
from dotenv import load_dotenv
import os
from config.handlers import router
from admin.state_book_handlers import admin_router
from admin.edit_texts_handlers import admin_texts_router
from admin.edit_great import admin_great_router
from admin.rigister_admin import register_admin_router
from data.models import initialize_db, db
from aiogram.filters import Command
from config.keyboards import commands

load_dotenv(".env")

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise ValueError("TOKEN environment variable not set. Please create a .env file with TOKEN=YOUR_BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


dp.include_router(admin_router)
dp.include_router(router)
dp.include_router(admin_texts_router)
dp.include_router(admin_great_router)
dp.include_router(register_admin_router)

print(f"DEBUG: commands keyboard content at startup: {commands.keyboard}")

async def main():
    db.init('books.db')
    db.connect()
    initialize_db()
    try:
        # Установка списка команд для бота
        commands_for_bot = [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Получить помощь")
        ]
        await bot.set_my_commands(commands=commands_for_bot, scope=BotCommandScopeAllPrivateChats())

        await dp.start_polling(bot)
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    asyncio.run(main())
