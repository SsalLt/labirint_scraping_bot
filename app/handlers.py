from aiogram.types.input_file import FSInputFile, BufferedInputFile
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import F, Router
from pathlib import Path
from io import BytesIO
import json
import csv
from scraping_core.get_categories import update_categories
from scraping_core.get_category_info import collect_data
from app.my_states import ParseState
import app.keyboards as kb

router = Router()
user_data_cache: dict = {}


@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Привет, {message.from_user.full_name}!\n"
                         f"Это бот для парсинга товаров с сайта labirint.ru",
                         reply_markup=kb.main)


@router.message(F.text == "🔢 Получить список категорий")
async def get_categories(message: Message):
    file_path = Path(__file__).parent.parent / "categories.json"

    if file_path.exists():
        json_file = FSInputFile(file_path, filename="categories.json")
        await message.answer_document(
            document=json_file,
            caption="Список категорий в формате JSON",
            reply_markup=kb.categories_list_kb
        )
    else:
        await message.answer("❌ Список категорий не найден. Попробуйте позже.")


@router.callback_query(F.data == "csv_format")
async def get_categories_as_csv(callback: CallbackQuery):
    file_path = Path(__file__).parent.parent / "categories.csv"

    if file_path.exists():
        csv_file = FSInputFile(file_path, filename="categories.csv")
        await callback.answer()
        await callback.message.answer_document(
            document=csv_file,
            caption="Список категорий в формате CSV"
        )
    else:
        await callback.answer()
        await callback.message.answer("❌ Список категорий не найден. Попробуйте позже.")


@router.callback_query(F.data == "txt_format")
async def get_categories_as_txt(callback: CallbackQuery):
    file_path = Path(__file__).parent.parent / "categories.txt"

    if file_path.exists():
        txt_file = FSInputFile(file_path, filename="categories.txt")
        await callback.answer()
        await callback.message.answer_document(
            document=txt_file,
            caption="Список категорий в формате TXT"
        )
    else:
        await callback.answer()
        await callback.message.answer("❌ Список категорий не найден. Попробуйте позже.")


@router.message(Command("update_categories"))
async def update_categories_handler(message: Message):
    await message.answer("⏳ Обновляю список категорий... Это может занять некоторое время")
    await update_categories()
    await message.answer("✅ Список категорий обновлен")


@router.message(F.text == "📚 Получить список товаров по категории")
async def handle_category_request(message: Message, state: FSMContext):
    await message.answer("🔢 Введите номер категории:")
    await state.set_state(ParseState.waiting_genre)


@router.message(ParseState.waiting_genre)
async def process_genre(message: Message, state: FSMContext):
    try:
        genre_id: int = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Номер категории должен быть числом. Повторите ввод:")
        return

    await message.answer("⏳ Сбор данных запущен, это может занять некоторое время...")

    try:
        data: list[dict] = await collect_data(genre_id)
        user_data_cache[genre_id] = data

        json_file = BytesIO()
        json_file.write(json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))
        json_file.seek(0)

        await message.answer_document(
            BufferedInputFile(
                json_file.read(),
                filename=f"labirint_{genre_id}.json"
            ),
            caption="✅ Готово!",
            reply_markup=kb.csv_inline(genre_id=genre_id)
        )

    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")
    finally:
        await state.clear()
