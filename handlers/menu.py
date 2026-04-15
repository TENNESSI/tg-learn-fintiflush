from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import figures_kb, main_menu_kb
from storage import user_sessions
from texts import HELP_TEXT

router = Router()


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
    session = user_sessions.get(message.from_user.id)

    if not session:
        await message.answer(
            "Статистика пока пустая. Сначала реши хотя бы одну тему."
        )
        return

    total_answered = session["correct"] + session["wrong"]
    percent = 0
    if total_answered > 0:
        percent = round(session["correct"] / total_answered * 100)

    await message.answer(
        "Моя статистика:\n\n"
        f"Последняя тема: {session['figure']}\n"
        f"Верно: {session['correct']}\n"
        f"Неверно: {session['wrong']}\n"
        f"Точность: {percent}%"
    )


@router.message(F.text == "Смешанный режим")
async def mixed_mode(message: Message) -> None:
    await message.answer("Смешанный режим пока не реализован.")


@router.message(F.text == "Справка")
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT)
