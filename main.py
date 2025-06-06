import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from dotenv import load_dotenv
import os
from config.handlers import router

load_dotenv(".env")

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()
dp.include_router(router)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
