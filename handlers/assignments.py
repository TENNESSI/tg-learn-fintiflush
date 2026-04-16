from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from config import TEACHER_IDS
from database import (
    add_assignment_attachment,
    add_submission_attachment,
    create_assignment,
    ensure_user,
    get_assignment_for_student,
    get_assignment_for_teacher,
    get_student_assignments,
    get_students,
    get_teacher_submitted_assignments,
    get_user_role,
    review_submission,
    save_submission_text,
    get_teacher_reviewed_assignments,
    get_user_full_name,
    get_user_stats
)
from keyboards import (
    assignment_submit_kb,
    assignments_list_kb,
    students_kb,
    teacher_menu_kb,
    teacher_review_decision_kb,
    teacher_reviews_kb,
    teacher_students_stats_kb
)
from storage import dialog_states
from keyboards import main_menu_kb

router = Router()

STATUS_LABELS = {
    "new": "не начато",
    "submitted": "ожидает проверки",
    "reviewed": "проверено",
}


FIGURE_NAMES = {
    "triangle": "Треугольник",
    "parallelogram": "Параллелограмм",
    "rhombus": "Ромб",
    "trapezoid": "Трапеция",
}


def format_student_stats_text(student_name: str, stats: dict[str, dict[str, int]]) -> str:
    total_correct = 0
    total_wrong = 0

    lines = [f"Статистика ученика: {student_name}\n"]

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


@router.callback_query(F.data.startswith("student_stats:"))
async def show_student_stats(callback: CallbackQuery) -> None:
    if not _teacher_access(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    if get_user_role(callback.from_user.id) != "teacher":
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])

    student_name = get_user_full_name(student_id) or f"id {student_id}"
    stats = get_user_stats(student_id)

    await callback.answer()
    await callback.message.answer(
        format_student_stats_text(student_name, stats)
    )


def _assignment_title(item: dict) -> str:
    parts = [f"Задание #{item['id']}"]
    if item.get("teacher_name"):
        parts.append(f"от {item['teacher_name']}")
    parts.append(f"[{STATUS_LABELS.get(item['status'], item['status'])}]")
    return " ".join(parts)


def _teacher_access(user_id: int) -> bool:
    return user_id in TEACHER_IDS


async def _send_media_bundle(
    message: Message,
    text: str | None,
    attachments: list[dict],
) -> None:
    if text:
        await message.answer(text)

    for attachment in attachments:
        if attachment["file_type"] == "photo":
            await message.answer_photo(
                attachment["file_id"],
                caption=attachment.get("caption"),
            )
        elif attachment["file_type"] == "document":
            await message.answer_document(
                attachment["file_id"],
                caption=attachment.get("caption"),
            )


async def _send_media_bundle_callback(
    callback: CallbackQuery,
    text: str | None,
    attachments: list[dict],
) -> None:
    if text:
        await callback.message.answer(text)

    for attachment in attachments:
        if attachment["file_type"] == "photo":
            await callback.message.answer_photo(
                attachment["file_id"],
                caption=attachment.get("caption"),
            )
        elif attachment["file_type"] == "document":
            await callback.message.answer_document(
                attachment["file_id"],
                caption=attachment.get("caption"),
            )


@router.message(F.text == "Выбрать ученика")
async def choose_student(message: Message) -> None:
    if not _teacher_access(message.from_user.id):
        await message.answer("У тебя нет доступа к режиму учителя.")
        return

    if get_user_role(message.from_user.id) != "teacher":
        return

    students = [s for s in get_students() if s["telegram_id"] != message.from_user.id]
    if not students:
        await message.answer("Пока нет учеников в базе. Пусть ученик сначала нажмёт /start.")
        return

    await message.answer(
        "Выбери ученика, которому отправить задание:",
        reply_markup=students_kb(students),
    )


@router.callback_query(F.data.startswith("pick_student:"))
async def pick_student(callback: CallbackQuery) -> None:
    if not _teacher_access(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    if get_user_role(callback.from_user.id) != "teacher":
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])

    dialog_states[callback.from_user.id] = {
        "state": "awaiting_assignment_content",
        "student_id": student_id,
    }

    await callback.answer()
    await callback.message.answer(
        "Теперь отправь задание одним сообщением: текстом, фото или файлом.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(
    lambda message: dialog_states.get(message.from_user.id, {}).get("state") == "awaiting_assignment_content"
)
async def receive_assignment_content(message: Message) -> None:
    if not _teacher_access(message.from_user.id):
        await message.answer("У тебя нет доступа к режиму учителя.")
        dialog_states.pop(message.from_user.id, None)
        return

    state = dialog_states.get(message.from_user.id)
    if not state:
        return

    teacher_id = message.from_user.id
    student_id = state["student_id"]

    text = message.text or message.caption
    assignment_id = create_assignment(
        teacher_id=teacher_id,
        student_id=student_id,
        text=text,
    )

    if message.photo:
        file_id = message.photo[-1].file_id
        add_assignment_attachment(
            assignment_id,
            file_id,
            "photo",
            message.caption,
        )
    elif message.document:
        add_assignment_attachment(
            assignment_id,
            message.document.file_id,
            "document",
            message.caption,
        )

    dialog_states.pop(message.from_user.id, None)
    await message.answer(
        "Задание сохранено и отправлено ученику.",
        reply_markup=teacher_menu_kb(),
    )


@router.message(F.text == "Мои задания")
async def my_assignments(message: Message) -> None:
    if get_user_role(message.from_user.id) != "student":
        return

    ensure_user(
        message.from_user.id,
        full_name=message.from_user.full_name,
    )

    assignments = get_student_assignments(message.from_user.id)
    if not assignments:
        await message.answer("У тебя пока нет заданий от учителя.")
        return

    lines = ["Мои задания:\n"]
    for item in assignments:
        lines.append(_assignment_title(item))

    await message.answer(
        "\n".join(lines),
        reply_markup=assignments_list_kb(assignments),
    )


@router.callback_query(F.data.startswith("open_assignment:"))
async def open_assignment(callback: CallbackQuery) -> None:
    data = get_assignment_for_student(
        int(callback.data.split(":")[1]),
        callback.from_user.id,
    )

    if data is None:
        await callback.answer("Задание не найдено.")
        return

    await callback.answer()
    await callback.message.answer(
        f"Задание #{data['id']} от {data['teacher_name']}\n"
        f"Статус: {STATUS_LABELS.get(data['status'], data['status'])}"
    )

    await _send_media_bundle_callback(
        callback,
        data.get("text"),
        data["attachments"],
    )

    submission = data.get("submission")
    if submission is None:
        await callback.message.answer(
            "Решение ещё не отправлено.",
            reply_markup=assignment_submit_kb(data["id"]),
        )
        return

    await callback.message.answer("Твоё решение уже отправлено.")
    await _send_media_bundle_callback(
        callback,
        submission.get("text"),
        submission["attachments"],
    )

    if data["status"] == "reviewed":
        mark = "✅ Верно" if submission.get("is_correct") == 1 else "❌ Неверно"
        await callback.message.answer(f"Проверка учителя: {mark}")


@router.callback_query(F.data.startswith("submit_assignment:"))
async def start_submission(callback: CallbackQuery) -> None:
    assignment_id = int(callback.data.split(":")[1])

    data = get_assignment_for_student(assignment_id, callback.from_user.id)
    if data is None:
        await callback.answer("Задание не найдено.")
        return

    if data["status"] == "reviewed":
        await callback.answer("Задание уже проверено. Повторно отправить нельзя.")
        return

    dialog_states[callback.from_user.id] = {
        "state": "awaiting_submission_content",
        "assignment_id": assignment_id,
    }

    await callback.answer()
    await callback.message.answer(
        "Отправь решение одним сообщением: текстом, фото или файлом.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(
    lambda message: dialog_states.get(message.from_user.id, {}).get("state") == "awaiting_submission_content"
)
async def receive_submission_content(message: Message) -> None:
    state = dialog_states.get(message.from_user.id)
    if not state:
        return

    assignment_id = state["assignment_id"]
    student_id = message.from_user.id

    if message.text:
        save_submission_text(assignment_id, student_id, message.text)
    elif message.caption:
        save_submission_text(assignment_id, student_id, message.caption)

    if message.photo:
        add_submission_attachment(
            assignment_id,
            student_id,
            message.photo[-1].file_id,
            "photo",
            message.caption,
        )
    elif message.document:
        add_submission_attachment(
            assignment_id,
            student_id,
            message.document.file_id,
            "document",
            message.caption,
        )

    dialog_states.pop(message.from_user.id, None)
    await message.answer(
        "Решение отправлено учителю.",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "Новые решения")
async def review_queue(message: Message) -> None:
    if not _teacher_access(message.from_user.id):
        await message.answer("У тебя нет доступа к режиму учителя.")
        return

    if get_user_role(message.from_user.id) != "teacher":
        return

    assignments = get_teacher_submitted_assignments(message.from_user.id)
    if not assignments:
        await message.answer("Новых решений пока нет.")
        return

    await message.answer(
        "Новые решения:",
        reply_markup=teacher_reviews_kb(assignments, reviewed=False),
    )


@router.message(F.text == "Проверенные")
async def reviewed_queue(message: Message) -> None:
    if not _teacher_access(message.from_user.id):
        await message.answer("У тебя нет доступа к режиму учителя.")
        return

    if get_user_role(message.from_user.id) != "teacher":
        return

    assignments = get_teacher_reviewed_assignments(message.from_user.id)
    if not assignments:
        await message.answer("Проверенных решений пока нет.")
        return

    await message.answer(
        "Проверенные решения:",
        reply_markup=teacher_reviews_kb(assignments, reviewed=True),
    )


@router.message(F.text == "Статистика")
async def students_stats_menu(message: Message) -> None:
    if not _teacher_access(message.from_user.id):
        await message.answer("У тебя нет доступа к режиму учителя.")
        return

    if get_user_role(message.from_user.id) != "teacher":
        return

    students = [s for s in get_students() if s["telegram_id"] != message.from_user.id]

    if not students:
        await message.answer("Пока нет учеников в базе.")
        return

    await message.answer(
        "Выбери ученика:",
        reply_markup=teacher_students_stats_kb(students),
    )


@router.callback_query(F.data.startswith("review_assignment:"))
async def review_assignment(callback: CallbackQuery) -> None:
    if not _teacher_access(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    data = get_assignment_for_teacher(
        int(callback.data.split(":")[1]),
        callback.from_user.id,
    )

    if data is None or data.get("submission") is None:
        await callback.answer("Решение не найдено.")
        return

    await callback.answer()
    await callback.message.answer(
        f"Задание #{data['id']} для {data['student_name']}"
    )

    await _send_media_bundle_callback(
        callback,
        data.get("text"),
        data["attachments"],
    )

    await callback.message.answer("Решение ученика:")
    await _send_media_bundle_callback(
        callback,
        data["submission"].get("text"),
        data["submission"]["attachments"],
    )

    await callback.message.answer(
        "Оцени решение:",
        reply_markup=teacher_review_decision_kb(data["id"]),
    )


@router.callback_query(F.data.startswith("mark_submission:"))
async def mark_submission(callback: CallbackQuery, bot: Bot) -> None:
    if not _teacher_access(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    _, assignment_id_text, result = callback.data.split(":")
    assignment_id = int(assignment_id_text)
    is_correct = result == "correct"

    student_id = review_submission(
        assignment_id,
        callback.from_user.id,
        is_correct,
    )

    if student_id is None:
        await callback.answer("Не удалось сохранить оценку.")
        return

    await callback.answer("Оценка сохранена.")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Готово.",
        reply_markup=teacher_menu_kb(),
    )

    verdict = (
        "✅ Учитель отметил решение как верное."
        if is_correct
        else "❌ Учитель отметил решение как неверное."
    )

    await bot.send_message(
        student_id,
        f"Задание #{assignment_id} проверено.\n{verdict}",
        reply_markup=main_menu_kb(),
    )