import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

from keyboards import main_menu_kb, figures_kb
from texts import HELP_TEXT

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я учебный бот по геометрическим фигурам.\n"
        "Выбери нужный раздел:",
        reply_markup=main_menu_kb()
    )


@dp.message(F.text == "Выбрать фигуру")
async def choose_figure(message: Message):
    await message.answer(
        "Выбери фигуру:",
        reply_markup=figures_kb()
    )


@dp.message(F.text == "Треугольник")
async def triangle_block(message: Message):
    await message.answer(
        "Раздел: Треугольник\n\n"
        "Здесь будет теория и задачи по треугольнику."
    )


@dp.message(F.text == "Параллелограмм")
async def parallelogram_block(message: Message):
    await message.answer(
        "Раздел: Параллелограмм\n\n"
        "Здесь будет теория и задачи по параллелограмму."
    )


@dp.message(F.text == "Ромб")
async def rhombus_block(message: Message):
    await message.answer(
        "Раздел: Ромб\n\n"
        "Здесь будет теория и задачи по ромбу."
    )


@dp.message(F.text == "Трапеция")
async def trapezoid_block(message: Message):
    await message.answer(
        "Раздел: Трапеция\n\n"
        "Здесь будет теория и задачи по трапеции."
    )


@dp.message(F.text == "Назад")
async def back_to_main(message: Message):
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu_kb()
    )


@dp.message(F.text == "Мои задания")
async def my_tasks(message: Message):
    await message.answer(
        "Здесь будут задания, которые назначил учитель.\n\n"
        "Пока список пуст."
    )


@dp.message(F.text == "Моя статистика")
async def my_stats(message: Message):
    await message.answer(
        "Моя статистика:\n\n"
        "Треугольник — 0%\n"
        "Параллелограмм — 0%\n"
        "Ромб — 0%\n"
        "Трапеция — 0%\n\n"
        "Общий прогресс — 0%"
    )


@dp.message(F.text == "Смешанный режим")
async def mixed_mode(message: Message):
    await message.answer(
        "Смешанный режим:\n"
        "здесь будут задачи по всем фигурам в случайном порядке."
    )


@dp.message(F.text == "Справка")
async def help_handler(message: Message):
    await message.answer(HELP_TEXT)


async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())