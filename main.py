import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from database import init_db
from handlers.assignments import router as assignments_router
from handlers.menu import router as menu_router
from handlers.practice import router as practice_router
from handlers.theory import router as theory_router
from config import BOT_TOKEN

load_dotenv()


def validate_token() -> None:
    if not BOT_TOKEN:
        raise ValueError("Переменная окружения BOT_TOKEN не найдена. Проверь .env")


async def main() -> None:
    validate_token()
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(menu_router)
    dp.include_router(theory_router)
    dp.include_router(practice_router)
    dp.include_router(assignments_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
