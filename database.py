import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).with_name("bot.db")
FIGURES = ("triangle", "parallelogram", "rhombus", "trapezoid")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                role TEXT NOT NULL DEFAULT 'student',
                full_name TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                text TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(telegram_id),
                FOREIGN KEY (student_id) REFERENCES users(telegram_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assignment_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_type TEXT NOT NULL,
                caption TEXT,
                FOREIGN KEY (assignment_id) REFERENCES assignments(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL UNIQUE,
                student_id INTEGER NOT NULL,
                text TEXT,
                is_correct INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assignment_id) REFERENCES assignments(id),
                FOREIGN KEY (student_id) REFERENCES users(telegram_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS submission_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_type TEXT NOT NULL,
                caption TEXT,
                FOREIGN KEY (submission_id) REFERENCES submissions(id)
            )
            """
        )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_results (
                user_id INTEGER NOT NULL,
                task_id TEXT NOT NULL,
                figure TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, task_id),
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        """)

        conn.commit()


def ensure_user(user_id: int, role: str = "student", full_name: str | None = None) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (telegram_id, role, full_name) VALUES (?, ?, ?)",
            (user_id, role, full_name),
        )
        if full_name is not None:
            cursor.execute(
                "UPDATE users SET full_name = COALESCE(?, full_name) WHERE telegram_id = ?",
                (full_name, user_id),
            )

        for figure in FIGURES:
            cursor.execute(
                """
                INSERT OR IGNORE INTO stats (user_id, figure, correct, wrong)
                VALUES (?, ?, 0, 0)
                """,
                (user_id, figure),
            )
        conn.commit()


def get_user_full_name(user_id: int) -> str | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_name FROM users WHERE telegram_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()

    if row is None:
        return None

    return row[0]


def get_user_role(user_id: int) -> str:
    ensure_user(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE telegram_id = ?", (user_id,))
        row = cursor.fetchone()
    return row["role"] if row else "student"


def set_user_role(user_id: int, role: str, full_name: str | None = None) -> None:
    ensure_user(user_id, role=role, full_name=full_name)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET role = ?, full_name = COALESCE(?, full_name) WHERE telegram_id = ?",
            (role, full_name, user_id),
        )
        conn.commit()


def get_students() -> list[dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT telegram_id, COALESCE(full_name, CAST(telegram_id AS TEXT)) AS full_name
            FROM users
            WHERE role = 'student'
            ORDER BY full_name COLLATE NOCASE
            """
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def save_task_result(user_id: int, task_id: str, figure: str, is_correct: bool) -> None:
    ensure_user(user_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO task_results (user_id, task_id, figure, is_correct)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, task_id)
            DO UPDATE SET
                figure = excluded.figure,
                is_correct = excluded.is_correct,
                updated_at = CURRENT_TIMESTAMP
        """, (
            user_id,
            task_id,
            figure,
            1 if is_correct else 0,
        ))
        conn.commit()


def get_user_stats(user_id: int) -> dict[str, dict[str, int]]:
    ensure_user(user_id)

    result = {
        "triangle": {"correct": 0, "wrong": 0},
        "parallelogram": {"correct": 0, "wrong": 0},
        "rhombus": {"correct": 0, "wrong": 0},
        "trapezoid": {"correct": 0, "wrong": 0},
    }

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                figure,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS correct,
                SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) AS wrong
            FROM task_results
            WHERE user_id = ?
            GROUP BY figure
        """, (user_id,))
        rows = cursor.fetchall()

    for figure, correct, wrong in rows:
        result[figure] = {
            "correct": correct or 0,
            "wrong": wrong or 0,
        }

    return result


def create_assignment(
    teacher_id: int,
    student_id: int,
    text: str | None = None,
) -> int:
    ensure_user(teacher_id, role="teacher")
    ensure_user(student_id, role="student")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assignments (teacher_id, student_id, text)
            VALUES (?, ?, ?)
            """,
            (teacher_id, student_id, text),
        )
        assignment_id = cursor.lastrowid
        conn.commit()
    return int(assignment_id)


def add_assignment_attachment(
    assignment_id: int,
    file_id: str,
    file_type: str,
    caption: str | None = None,
) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assignment_attachments (assignment_id, file_id, file_type, caption)
            VALUES (?, ?, ?, ?)
            """,
            (assignment_id, file_id, file_type, caption),
        )
        conn.commit()


def _get_assignment_attachments(assignment_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_id, file_type, caption FROM assignment_attachments WHERE assignment_id = ? ORDER BY id",
            (assignment_id,),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def _get_submission_attachments(submission_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_id, file_type, caption FROM submission_attachments WHERE submission_id = ? ORDER BY id",
            (submission_id,),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_student_assignments(student_id: int) -> list[dict[str, Any]]:
    ensure_user(student_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.id,
                   a.status,
                   a.text,
                   a.created_at,
                   COALESCE(u.full_name, CAST(a.teacher_id AS TEXT)) AS teacher_name,
                   EXISTS(SELECT 1 FROM assignment_attachments att WHERE att.assignment_id = a.id) AS has_attachments,
                   s.id AS submission_id,
                   s.is_correct
            FROM assignments a
            LEFT JOIN users u ON u.telegram_id = a.teacher_id
            LEFT JOIN submissions s ON s.assignment_id = a.id
            WHERE a.student_id = ?
            ORDER BY a.id DESC
            """,
            (student_id,),
        )
        rows = cursor.fetchall()

    result = []
    for row in rows:
        item = dict(row)
        item["has_attachments"] = bool(item["has_attachments"])
        result.append(item)
    return result


def get_teacher_submitted_assignments(teacher_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.student_id, u.full_name
            FROM assignments a
            JOIN users u ON u.telegram_id = a.student_id
            WHERE a.teacher_id = ? AND a.status = 'submitted'
            ORDER BY a.id DESC
        """, (teacher_id,))
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "student_id": row[1],
            "student_name": row[2],
        }
        for row in rows
    ]


def get_teacher_reviewed_assignments(teacher_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.student_id, u.full_name
            FROM assignments a
            JOIN users u ON u.telegram_id = a.student_id
            WHERE a.teacher_id = ? AND a.status = 'reviewed'
            ORDER BY a.id DESC
        """, (teacher_id,))
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "student_id": row[1],
            "student_name": row[2],
        }
        for row in rows
    ]


def get_assignment_for_student(assignment_id: int, student_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.id,
                   a.teacher_id,
                   a.student_id,
                   a.text,
                   a.status,
                   a.created_at,
                   COALESCE(u.full_name, CAST(a.teacher_id AS TEXT)) AS teacher_name
            FROM assignments a
            LEFT JOIN users u ON u.telegram_id = a.teacher_id
            WHERE a.id = ? AND a.student_id = ?
            """,
            (assignment_id, student_id),
        )
        row = cursor.fetchone()
    if row is None:
        return None

    data = dict(row)
    data["attachments"] = _get_assignment_attachments(assignment_id)
    data["submission"] = get_submission_by_assignment(assignment_id)
    return data


def get_assignment_for_teacher(assignment_id: int, teacher_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.id,
                   a.teacher_id,
                   a.student_id,
                   a.text,
                   a.status,
                   a.created_at,
                   COALESCE(u.full_name, CAST(a.student_id AS TEXT)) AS student_name
            FROM assignments a
            LEFT JOIN users u ON u.telegram_id = a.student_id
            WHERE a.id = ? AND a.teacher_id = ?
            """,
            (assignment_id, teacher_id),
        )
        row = cursor.fetchone()
    if row is None:
        return None

    data = dict(row)
    data["attachments"] = _get_assignment_attachments(assignment_id)
    data["submission"] = get_submission_by_assignment(assignment_id)
    return data


def _ensure_submission(assignment_id: int, student_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM submissions WHERE assignment_id = ?",
            (assignment_id,),
        )
        row = cursor.fetchone()
        if row is not None:
            return int(row["id"])

        cursor.execute(
            "INSERT INTO submissions (assignment_id, student_id, text) VALUES (?, ?, NULL)",
            (assignment_id, student_id),
        )
        submission_id = cursor.lastrowid
        conn.commit()
    return int(submission_id)


def save_submission_text(assignment_id: int, student_id: int, text: str) -> int:
    submission_id = _ensure_submission(assignment_id, student_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT text FROM submissions WHERE id = ?",
            (submission_id,),
        )
        row = cursor.fetchone()
        existing_text = row["text"] if row and row["text"] else ""
        new_text = f"{existing_text}\n\n{text}".strip() if existing_text else text

        cursor.execute(
            """
            UPDATE submissions
            SET text = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_text, submission_id),
        )
        cursor.execute(
            "UPDATE assignments SET status = 'submitted', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (assignment_id,),
        )
        conn.commit()
    return submission_id


def add_submission_attachment(
    assignment_id: int,
    student_id: int,
    file_id: str,
    file_type: str,
    caption: str | None = None,
) -> int:
    submission_id = _ensure_submission(assignment_id, student_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO submission_attachments (submission_id, file_id, file_type, caption)
            VALUES (?, ?, ?, ?)
            """,
            (submission_id, file_id, file_type, caption),
        )
        cursor.execute(
            "UPDATE submissions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (submission_id,),
        )
        cursor.execute(
            "UPDATE assignments SET status = 'submitted', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (assignment_id,),
        )
        conn.commit()
    return submission_id


def get_submission_by_assignment(assignment_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, student_id, text, is_correct, created_at, updated_at FROM submissions WHERE assignment_id = ?",
            (assignment_id,),
        )
        row = cursor.fetchone()
    if row is None:
        return None

    data = dict(row)
    data["attachments"] = _get_submission_attachments(data["id"])
    return data


def review_submission(assignment_id: int, teacher_id: int, is_correct: bool) -> int | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_id FROM assignments WHERE id = ? AND teacher_id = ?",
            (assignment_id, teacher_id),
        )
        owner_row = cursor.fetchone()
        if owner_row is None:
            return None

        cursor.execute(
            "UPDATE submissions SET is_correct = ?, updated_at = CURRENT_TIMESTAMP WHERE assignment_id = ?",
            (1 if is_correct else 0, assignment_id),
        )
        if cursor.rowcount == 0:
            return None

        cursor.execute(
            "UPDATE assignments SET status = 'reviewed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (assignment_id,),
        )
        conn.commit()
        return int(owner_row["student_id"])
