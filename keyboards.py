from typing import Any

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def student_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Выбрать фигуру"),
                KeyboardButton(text="Мои задания"),
            ],
            [
                KeyboardButton(text="Моя статистика"),
                KeyboardButton(text="Смешанный режим"),
            ],
            [KeyboardButton(text="Справка")],
        ],
        resize_keyboard=True,
    )


# для совместимости со старым кодом
main_menu_kb = student_menu_kb


def teacher_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Выбрать ученика"),
                KeyboardButton(text="Новые решения"),
            ],
            [
                KeyboardButton(text="Проверенные"),
                KeyboardButton(text="Статистика"),
            ],
            [
                KeyboardButton(text="Режим ученика"),
            ]
        ],
        resize_keyboard=True,
    )


def teacher_students_stats_kb(students: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for student in students:
        rows.append([
            InlineKeyboardButton(
                text=student["full_name"],
                callback_data=f"student_stats:{student['telegram_id']}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def figures_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Треугольник"),
                KeyboardButton(text="Параллелограмм"),
            ],
            [KeyboardButton(text="Ромб"), KeyboardButton(text="Трапеция")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def theory_start_kb(figure: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Начать задачи",
                    callback_data=f"start_tasks:{figure}",
                )
            ]
        ]
    )


def answer_options_kb(task_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="А", callback_data=f"answer:{task_id}:A"),
                InlineKeyboardButton(text="Б", callback_data=f"answer:{task_id}:B"),
            ],
            [
                InlineKeyboardButton(text="В", callback_data=f"answer:{task_id}:C"),
                InlineKeyboardButton(text="Г", callback_data=f"answer:{task_id}:D"),
            ],
        ]
    )


def next_task_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Следующая задача", callback_data="next_task")]
        ]
    )


def students_kb(students: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=str(student["full_name"]),
                callback_data=f"pick_student:{student['telegram_id']}",
            )
        ]
        for student in students
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def assignments_list_kb(assignments: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    status_icons = {
        "new": "🆕",
        "submitted": "📨",
        "reviewed": "✅",
    }
    rows = [
        [
            InlineKeyboardButton(
                text=f"{status_icons.get(item['status'], '📘')} Задание #{item['id']}",
                callback_data=f"open_assignment:{item['id']}",
            )
        ]
        for item in assignments
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def teacher_reviews_kb(assignments: list[dict], reviewed: bool = False) -> InlineKeyboardMarkup:
    icon = "✅" if reviewed else "🆕"

    rows = []
    for item in assignments:
        rows.append([
            InlineKeyboardButton(
                text=f"{icon} {item['student_name']} — задание #{item['id']}",
                callback_data=f"review_assignment:{item['id']}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def assignment_submit_kb(assignment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отправить решение",
                    callback_data=f"submit_assignment:{assignment_id}",
                )
            ]
        ]
    )


def teacher_review_decision_kb(assignment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Верно",
                    callback_data=f"mark_submission:{assignment_id}:correct",
                ),
                InlineKeyboardButton(
                    text="❌ Неверно",
                    callback_data=f"mark_submission:{assignment_id}:wrong",
                ),
            ]
        ]
    )
