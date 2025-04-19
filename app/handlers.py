import aiohttp
from aiogram.types.input_file import FSInputFile, BufferedInputFile
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import F, Router
from pathlib import Path
from io import BytesIO, StringIO
import json
import csv

from config import LRUDict
from scraping_core.scraping_functions import get_category_name
from scraping_core.get_categories import update_categories
from scraping_core.get_category_info import collect_data
from app.my_states import ParseState, ParseGenreForCheck
import app.keyboards as kb

router = Router()
user_data_cache: LRUDict = LRUDict(max_size=20)


@router.message(Command("start"))
@router.message(F.text == "Назад ↩")
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Привет, {message.from_user.full_name}!\n"
                         f"Это бот для парсинга товаров с сайта labirint.ru",
                         reply_markup=kb.main)


@router.message(F.text == "🔢 Получить список категорий")
@router.message(Command("all_categories"))
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
@router.message(Command("category_articles"))
async def handle_category_request(message: Message, state: FSMContext):
    await message.answer("🔢 Введите номер категории:", reply_markup=kb.back_to_main)
    await state.set_state(ParseState.waiting_genre)


@router.message(ParseState.waiting_genre)
async def process_genre(message: Message, state: FSMContext):
    try:
        genre_id: int = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Номер категории должен быть числом. Повторите ввод:")
        return

    try:
        category: None | tuple[str, dict] = user_data_cache.get(genre_id)
        if category:
            category_name, data = category
        else:
            await message.answer("⏳ Сбор данных запущен, это может занять некоторое время...",
                                 reply_markup=kb.remove)

            category: None | tuple[str, dict] = await collect_data(genre_id)
            if not category:
                await message.answer("❌ Ошибка при сборе данных.\n"
                                     "Попробуйте позже или проверьте наличие категории "
                                     f"(Командой /get_category_name или по ссылке https://www.labirint.ru/genres/{genre_id}/).",
                                     reply_markup=kb.main)
                return
            category_name, data = category
            user_data_cache[genre_id] = category_name, data

        await message.answer("✅ Данные успешно собраны", reply_markup=kb.main)
        await message.answer_document(
            BufferedInputFile(
                json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'),
                filename=f"labirint_genre_{genre_id}.json",
            ),
            caption=category_name,
            reply_markup=kb.csv_inline(genre_id=genre_id)
        )

    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}", reply_markup=kb.main)
    finally:
        await state.clear()


@router.callback_query(F.data.startswith("csv_"))
async def send_csv(callback: CallbackQuery):
    genre_id: int = int(callback.data.split("_")[1])
    category: None | tuple[str, dict] = user_data_cache.get(genre_id)

    if not category:
        await callback.answer()
        await callback.message.answer("🚫 Данные устарели или отсутствуют.")
        return

    try:
        category_name, data = category
        text_buffer = StringIO()
        text_buffer.write('\ufeff')  # Добавление BOM для Excel
        writer = csv.writer(
            text_buffer,
            delimiter=';',
            quoting=csv.QUOTE_ALL,  # экранирование всех значения
            lineterminator='\r\n'  # правильные переводы строк для Windows
        )

        writer.writerow([
            'Название', 'Ссылка', 'Автор',
            'Издательство', 'Цена', 'Старая цена', 'Скидка'
        ])

        for item in data:
            writer.writerow([
                str(item.get('book_title', '')).replace(';', ','),
                str(item.get('book_link', '')),
                str(item.get('book_author', '')),
                str(item.get('book_publishing', '')),
                str(item.get('book_discounted_price', '')),
                str(item.get('book_old_price', '')),
                str(item.get('book_sale', ''))
            ])

        csv_data = text_buffer.getvalue().encode('utf-8-sig')  # Явное указание BOM

        bytes_buffer = BytesIO(csv_data)
        bytes_buffer.seek(0)

        await callback.message.answer_document(
            BufferedInputFile(
                bytes_buffer.read(),
                filename=f"labirint_genre_{genre_id}.csv"
            )
        )
        await callback.answer()

    except Exception as e:
        await callback.answer(f"⚠️ Ошибка: {str(e)}", show_alert=True)


@router.message(F.text == "📝 Название категории по номеру")
@router.message(Command("get_category_name"))
async def get_category_name_handler(message: Message, state: FSMContext):
    await message.answer("🔢 Введите номер категории:", reply_markup=kb.back_to_main)
    await state.set_state(ParseGenreForCheck.waiting_genre)


@router.message(ParseGenreForCheck.waiting_genre)
async def process_genre(message: Message, state: FSMContext):
    try:
        genre_id: int = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Номер категории должен быть числом. Повторите ввод:")
        return

    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://www.labirint.ru/genres/{genre_id}"
            data: dict[int: str] | None = await get_category_name(session=session,
                                                                  url=url,
                                                                  page=genre_id)
            if not data:
                await message.answer("❌ Категория не найдена.",
                                     reply_markup=kb.main)
                return

        await message.answer(f"#⃣  Номер категории: {genre_id}\n"
                             f"📝 Название категории: {data.get(genre_id)}",
                             reply_markup=kb.main)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")
    finally:
        await state.clear()
