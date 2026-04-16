import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

raw_teacher_ids = os.getenv("TEACHER_IDS", "")
TEACHER_IDS = {
    int(item.strip())
    for item in raw_teacher_ids.split(",")
    if item.strip()
}