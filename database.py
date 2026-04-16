import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("bot.db")

FIGURES = ("triangle", "parallelogram", "rhombus", "trapezoid")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                user_id INTEGER NOT NULL,
                figure TEXT NOT NULL,
                correct INTEGER NOT NULL DEFAULT 0,
                wrong INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, figure),
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                mode TEXT NOT NULL,
                figure TEXT,
                task_ids TEXT NOT NULL,
                current_index INTEGER NOT NULL DEFAULT 0,
                correct INTEGER NOT NULL DEFAULT 0,
                wrong INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(telegram_id)
            )
        """)

        conn.commit()


def ensure_user(user_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)",
            (user_id,)
        )

        for figure in FIGURES:
            cursor.execute("""
                INSERT OR IGNORE INTO stats (user_id, figure, correct, wrong)
                VALUES (?, ?, 0, 0)
            """, (user_id, figure))

        conn.commit()


def add_answer_result(user_id: int, figure: str, is_correct: bool) -> None:
    ensure_user(user_id)

    column = "correct" if is_correct else "wrong"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE stats SET {column} = {column} + 1 WHERE user_id = ? AND figure = ?",
            (user_id, figure)
        )
        conn.commit()


def get_user_stats(user_id: int) -> dict[str, dict[str, int]]:
    ensure_user(user_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT figure, correct, wrong
            FROM stats
            WHERE user_id = ?
        """, (user_id,))
        rows = cursor.fetchall()

    return {
        figure: {"correct": correct, "wrong": wrong}
        for figure, correct, wrong in rows
    }