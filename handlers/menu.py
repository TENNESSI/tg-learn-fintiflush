from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import figures_kb, main_menu_kb
from storage import user_sessions
from texts import HELP_TEXT

router = Router()


FIGURE_LABELS = {
    "triangle": "Треугольник",
    "parallelogram": "Параллелограмм",
    "rhombus": "Ромб",
    "trapezoid": "Трапеция",
}


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

    if not session or not session.get("stats"):
        await message.answer("Статистика пока пустая. Сначала реши хотя бы одну задачу.")
        return

    stats = session["stats"]
    total_correct = sum(item["correct"] for item in stats.values())
    total_wrong = sum(item["wrong"] for item in stats.values())
    total_answered = total_correct + total_wrong

    if total_answered == 0:
        await message.answer("Статистика пока пустая. Сначала реши хотя бы одну задачу.")
        return

    total_percent = round(total_correct / total_answered * 100)

    lines = ["Моя статистика:\n"]

    for figure_code, figure_name in FIGURE_LABELS.items():
        figure_correct = stats[figure_code]["correct"]
        figure_wrong = stats[figure_code]["wrong"]
        figure_answered = figure_correct + figure_wrong

        if figure_answered == 0:
            figure_percent = 0
        else:
            figure_percent = round(figure_correct / figure_answered * 100)

        lines.append(
            f"{figure_name}: {figure_correct} верно, {figure_wrong} неверно, точность {figure_percent}%"
        )

    lines.append(
        f"\nОбщий результат: {total_correct} верно, {total_wrong} неверно, точность {total_percent}%"
    )

    await message.answer("\n".join(lines))


@router.message(F.text == "Смешанный режим")
async def mixed_mode(message: Message) -> None:
    await message.answer("Смешанный режим пока не реализован.")


@router.message(F.text == "Справка")
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT)
