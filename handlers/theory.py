from aiogram import F, Router
from aiogram.types import FSInputFile, Message

from keyboards import theory_start_kb
from texts import (
    PARALLELOGRAM_TEXT,
    RHOMBUS_TEXT,
    TRAPEZOID_TEXT,
    TRIANGLE_TEXT,
)

router = Router()


@router.message(F.text == "Треугольник")
async def triangle_block(message: Message) -> None:
    await message.answer(TRIANGLE_TEXT)
    await message.answer_photo(
        FSInputFile("assets/theory/triangle.png"),
        reply_markup=theory_start_kb("triangle"),
    )


@router.message(F.text == "Параллелограмм")
async def parallelogram_block(message: Message) -> None:
    await message.answer(PARALLELOGRAM_TEXT)
    await message.answer_photo(
        FSInputFile("assets/theory/parallelogram.png"),
        reply_markup=theory_start_kb("parallelogram"),
    )


@router.message(F.text == "Ромб")
async def rhombus_block(message: Message) -> None:
    await message.answer(RHOMBUS_TEXT)
    await message.answer_photo(
        FSInputFile("assets/theory/rhombus.png"),
        reply_markup=theory_start_kb("rhombus"),
    )


@router.message(F.text == "Трапеция")
async def trapezoid_block(message: Message) -> None:
    await message.answer(TRAPEZOID_TEXT)
    await message.answer_photo(
        FSInputFile("assets/theory/trapezoid.png"),
        reply_markup=theory_start_kb("trapezoid"),
    )
