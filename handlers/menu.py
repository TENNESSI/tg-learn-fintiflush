from aiogram import F, Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from keyboards import figures_kb, main_menu_kb
from storage import user_sessions
from texts import HELP_TEXT
from handlers.practice import send_current_task
from database import ensure_user, get_user_stats

router = Router()


FIGURE_NAMES = {
    "triangle": "Треугольник",
    "parallelogram": "Параллелограмм",
    "rhombus": "Ромб",
    "trapezoid": "Трапеция",
}


def format_stats_text(stats: dict[str, dict[str, int]]) -> str:
    total_correct = 0
    total_wrong = 0

    lines = ["Моя статистика:\n"]

    for figure in ("triangle", "parallelogram", "rhombus", "trapezoid"):
        correct = stats.get(figure, {}).get("correct", 0)
        wrong = stats.get(figure, {}).get("wrong", 0)
        total = correct + wrong
        accuracy = round(correct / total * 100) if total else 0

        total_correct += correct
        total_wrong += wrong

        lines.append(
            f"{FIGURE_NAMES[figure]}: {correct} верно, {wrong} неверно, точность {accuracy}%"
        )

    total_answers = total_correct + total_wrong
    total_accuracy = round(total_correct / total_answers * 100) if total_answers else 0

    lines.append("")
    lines.append(
        f"Общий результат: {total_correct} верно, {total_wrong} неверно, точность {total_accuracy}%"
    )

    return "\n".join(lines)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я учебный бот по геометрическим фигурам.\nВыбери нужный раздел:",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "Выбрать фигуру")
async def choose_figure(message: Message) -> None:
    await message.answer("Выбери фигуру:", reply_markup=figures_kb())


@router.message(F.text == "Назад")
async def back_to_main(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=main_menu_kb())


@router.message(F.text == "Мои задания")
async def my_tasks(message: Message) -> None:
    await message.answer("Здесь будут задания, которые назначил учитель.\n\nПока список пуст.")


@router.message(F.text == "Моя статистика")
async def my_stats(message: Message) -> None:
    user_id = message.from_user.id

    ensure_user(user_id)
    stats = get_user_stats(user_id)

    await message.answer(format_stats_text(stats))


@router.message(F.text == "Смешанный режим")
async def mixed_mode(message: Message, bot: Bot):
    user_id = message.from_user.id

    ensure_user(user_id)
    user_sessions[user_id] = {
        "mode": "mixed",
        "figure": None,
        "index": 0,
        "answered_task_ids": set(),
        "correct": 0,
        "wrong": 0,
        "task_ids": [],
    }

    await message.answer(
        "Смешанный режим запущен.",
        reply_markup=ReplyKeyboardRemove()
    )
    await send_current_task(message.chat.id, bot, user_id)


@router.message(F.text == "Справка")
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT)
