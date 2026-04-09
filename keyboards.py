from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Выбрать фигуру"),
                KeyboardButton(text="Мои задания")
            ],
            [
                KeyboardButton(text="Моя статистика"),
                KeyboardButton(text="Смешанный режим")
            ],
            [
                KeyboardButton(text="Справка")
            ]
        ],
        resize_keyboard=True
    )


def figures_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Треугольник"),
                KeyboardButton(text="Параллелограмм")
            ],
            [
                KeyboardButton(text="Ромб"),
                KeyboardButton(text="Трапеция")
            ],
            [
                KeyboardButton(text="Назад")
            ]
        ],
        resize_keyboard=True
    )


def theory_start_kb(figure: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Начать задачи",
                    callback_data=f"start_tasks:{figure}"
                )
            ]
        ]
    )


def answer_options_kb(task_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="А", callback_data=f"answer:{task_id}:A"),
                InlineKeyboardButton(text="Б", callback_data=f"answer:{task_id}:B")
            ],
            [
                InlineKeyboardButton(text="В", callback_data=f"answer:{task_id}:C"),
                InlineKeyboardButton(text="Г", callback_data=f"answer:{task_id}:D")
            ]
        ]
    )


def next_task_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Следующая задача", callback_data="next_task")]
        ]
    )