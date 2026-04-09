import asyncio
import os
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardRemove
from dotenv import load_dotenv

from keyboards import (
    main_menu_kb,
    figures_kb,
    theory_start_kb,
    answer_options_kb,
    next_task_kb
)
from texts import HELP_TEXT
from tasks import TASKS

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()


user_sessions = {}


def get_tasks_by_figure(figure: str) -> list[dict[str, Any]]:
    return [task for task in TASKS if task["figure"] == figure]


def format_task_text(task: dict, number: int, total: int, correct: int, wrong: int):
    return (
        f"Задача {number}/{total}\n"
        f"Верно: {correct} | Неверно: {wrong}\n\n"
        f"{task['question']}\n\n"
        f"А) {task['options']['A']}\n"
        f"Б) {task['options']['B']}\n"
        f"В) {task['options']['C']}\n"
        f"Г) {task['options']['D']}"
    )


async def send_current_task(chat_id: int, bot: Bot, user_id: int):
    session = user_sessions[user_id]
    figure_tasks = get_tasks_by_figure(session["figure"])
    index = session["index"]

    if index >= len(figure_tasks):
        await bot.send_message(
            chat_id,
            f"Задачи по теме закончились.\n\n"
            f"Итог:\n"
            f"Верно: {session['correct']}\n"
            f"Неверно: {session['wrong']}",
            reply_markup=main_menu_kb()
        )
        return

    task: dict[str, Any] = figure_tasks[index]

    await bot.send_message(
        chat_id,
        format_task_text(
            task,
            index + 1,
            len(figure_tasks),
            session["correct"],
            session["wrong"]
        ),
        reply_markup=answer_options_kb(task["id"])
    )


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
    await message.answer("Раздел: Треугольник\n\nКраткая теория по треугольнику:")
    await message.answer_photo(
        FSInputFile("assets/theory/triangle.png"),
        reply_markup=theory_start_kb("triangle")
    )


@dp.message(F.text == "Параллелограмм")
async def parallelogram_block(message: Message):
    await message.answer("Раздел: Параллелограмм\n\nКраткая теория по параллелограмму:")
    await message.answer_photo(
        FSInputFile("assets/theory/parallelogram.png"),
        reply_markup=theory_start_kb("parallelogram")
    )


@dp.message(F.text == "Ромб")
async def rhombus_block(message: Message):
    await message.answer("Раздел: Ромб\n\nКраткая теория по ромбу:")
    await message.answer_photo(
        FSInputFile("assets/theory/rhombus.png"),
        reply_markup=theory_start_kb("rhombus")
    )


@dp.message(F.text == "Трапеция")
async def trapezoid_block(message: Message):
    await message.answer("Раздел: Трапеция\n\nКраткая теория по трапеции:")
    await message.answer_photo(
        FSInputFile("assets/theory/trapezoid.png"),
        reply_markup=theory_start_kb("trapezoid")
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


@dp.callback_query(F.data.startswith("start_tasks:"))
async def start_tasks(callback: CallbackQuery, bot: Bot):
    figure = callback.data.split(":")[1]
    user_id = callback.from_user.id

    user_sessions[user_id] = {
        "figure": figure,
        "index": 0,
        "answered_task_ids": set(),
        "correct": 0,
        "wrong": 0,
    }

    await callback.answer()
    await callback.message.answer(
        "Начинаем задачи.",
        reply_markup=ReplyKeyboardRemove()
    )
    await send_current_task(callback.message.chat.id, bot, user_id)


@dp.callback_query(F.data.startswith("answer:"))
async def check_answer(callback: CallbackQuery, bot: Bot):
    _, task_id, selected_option = callback.data.split(":")
    user_id = callback.from_user.id

    if user_id not in user_sessions:
        await callback.answer("Сначала выбери фигуру.")
        return

    session = user_sessions[user_id]

    if task_id in session["answered_task_ids"]:
        await callback.answer("На этот вопрос уже ответили.")
        return

    task = next(task for task in TASKS if task["id"] == task_id)
    correct_option = task["correct_option"]

    session["answered_task_ids"].add(task_id)

    # убираем старые кнопки у этой задачи
    await callback.message.edit_reply_markup(reply_markup=None)

    if selected_option == correct_option:
        session["correct"] += 1
        text = (
            f"✅ Верно!\n\n"
            f"Правильный ответ: {correct_option}) {task['options'][correct_option]}\n\n"
            f"Решение:\n{task['solution']}"
        )
    else:
        session["wrong"] += 1
        text = (
            f"❌ Неверно.\n\n"
            f"Правильный ответ: {correct_option}) {task['options'][correct_option]}\n\n"
            f"Решение:\n{task['solution']}"
        )

    await callback.answer()
    await callback.message.answer(text, reply_markup=next_task_kb())


@dp.callback_query(F.data == "next_task")
async def next_task(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    if user_id not in user_sessions:
        await callback.answer("Сначала выбери фигуру.")
        return

    user_sessions[user_id]["index"] += 1

    await callback.answer()
    await send_current_task(callback.message.chat.id, bot, user_id)


async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

