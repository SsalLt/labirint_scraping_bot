from aiogram.types import (KeyboardButton, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove, InlineKeyboardButton,
                           InlineKeyboardMarkup)

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📚 Получить список товаров по категории")],
    [KeyboardButton(text="📝 Название категории по номеру")],
    [KeyboardButton(text="🔢 Получить список категорий")]
],
    resize_keyboard=True)

remove = ReplyKeyboardRemove()

back_to_main = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Назад ↩")]],
    resize_keyboard=True
)

categories_list_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬇️ В формате CSV", callback_data="csv_format")],
    [InlineKeyboardButton(text="⬇️ В формате TXT", callback_data="txt_format")]
])


def csv_inline(genre_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ В формате CSV", callback_data=f"csv_{genre_id}")]
    ])
