from typing import Any

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from keyboards import answer_options_kb, main_menu_kb, next_task_kb
from storage import empty_stats, user_sessions
from tasks import TASKS

import random

router = Router()


FIGURE_LABELS = {
    "triangle": "Треугольник",
    "parallelogram": "Параллелограмм",
    "rhombus": "Ромб",
    "trapezoid": "Трапеция",
}


def figure_name_ru(figure: str) -> str:
    names = {
        "triangle": "Треугольник",
        "parallelogram": "Параллелограмм",
        "rhombus": "Ромб",
        "trapezoid": "Трапеция",
    }
    return names.get(figure, figure)


def get_mixed_tasks():
    tasks = TASKS[:]
    random.shuffle(tasks)
    return tasks


def get_tasks_by_figure(figure: str) -> list[dict[str, Any]]:
    return [task for task in TASKS if task["figure"] == figure]


def format_task_text(
    task: dict[str, Any],
    number: int,
    total: int,
    correct: int,
    wrong: int,
) -> str:
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
    index = session["index"]

    if session["mode"] == "mixed":
        if not session["task_ids"]:
            mixed_tasks = get_mixed_tasks()
            session["task_ids"] = [task["id"] for task in mixed_tasks]

        if index >= len(session["task_ids"]):
            await bot.send_message(
                chat_id,
                f"Смешанный режим завершён.\n\n"
                f"Итог:\n"
                f"Верно: {session['correct']}\n"
                f"Неверно: {session['wrong']}",
                reply_markup=main_menu_kb()
            )
            return

        task_id = session["task_ids"][index]
        task = next(task for task in TASKS if task["id"] == task_id)

        await bot.send_message(
            chat_id,
            (
                f"Смешанный режим\n"
                f"Тема: {figure_name_ru(task['figure'])}\n\n"
                + format_task_text(
                    task,
                    index + 1,
                    len(session["task_ids"]),
                    session["correct"],
                    session["wrong"]
                )
            ),
            reply_markup=answer_options_kb(task["id"])
        )
        return

    figure_tasks = get_tasks_by_figure(session["figure"])

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

    task = figure_tasks[index]

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


@router.callback_query(F.data.startswith("start_tasks:"))
async def start_tasks(callback: CallbackQuery, bot: Bot) -> None:
    figure = callback.data.split(":")[1]
    user_id = callback.from_user.id

    existing_stats = user_sessions.get(user_id, {}).get("stats", empty_stats())

    user_sessions[user_id] = {
        "mode": "figure",
        "figure": figure,
        "index": 0,
        "answered_task_ids": set(),
        "correct": 0,
        "wrong": 0,
        "task_ids": [],
        "stats": existing_stats,
    }

    await callback.answer()
    await callback.message.answer(
        "Начинаем задачи.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_current_task(callback.message.chat.id, bot, user_id)


@router.callback_query(F.data.startswith("answer:"))
async def check_answer(callback: CallbackQuery) -> None:
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
    figure = task["figure"]
    figure_stats = session["stats"][figure]

    session["answered_task_ids"].add(task_id)
    await callback.message.edit_reply_markup(reply_markup=None)

    if selected_option == correct_option:
        session["correct"] += 1
        figure_stats["correct"] += 1

        text = (
            f"✅ Верно!\n\n"
            f"Правильный ответ: {correct_option}) {task['options'][correct_option]}\n\n"
            f"Решение:\n{task['solution']}"
        )
    else:
        session["wrong"] += 1
        figure_stats["wrong"] += 1

        text = (
            f"❌ Неверно.\n\n"
            f"Правильный ответ: {correct_option}) {task['options'][correct_option]}\n\n"
            f"Решение:\n{task['solution']}"
        )

    await callback.answer()
    await callback.message.answer(text, reply_markup=next_task_kb())


@router.callback_query(F.data == "next_task")
async def next_task(callback: CallbackQuery, bot: Bot) -> None:
    user_id = callback.from_user.id

    if user_id not in user_sessions:
        await callback.answer("Сначала выбери фигуру.")
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    user_sessions[user_id]["index"] += 1

    await callback.answer()
    await send_current_task(callback.message.chat.id, bot, user_id)
