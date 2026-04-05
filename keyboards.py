from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


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