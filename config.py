from aiogram.types import BotCommand
from dotenv import load_dotenv, find_dotenv
from collections import OrderedDict
from datetime import datetime
import os

load_dotenv(find_dotenv())

TOKEN = os.getenv("TOKEN")

my_commands: list[BotCommand] = [
    BotCommand(command="start", description="▶ Запустить бота"),
    BotCommand(command="category_articles", description="📚 Список товаров по категории"),
    BotCommand(command="get_category_name", description="📝 Название категории по номеру"),
    BotCommand(command="all_categories", description="📋 Список доступных категорий"),
]


class LRUDict(OrderedDict):
    """
    Словарь с автоматическим удалением старых записей при превышении лимита
    """

    def __init__(self, max_size: int = 100, *args, **kwargs):
        self.max_size: int = max_size
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._check_size()

    def _check_size(self):
        while len(self) > self.max_size:
            self.popitem(last=False)  # Удаляем самый старый элемент


def timer(func):
    async def wrapper(*args, **kwargs):
        start_time: float = datetime.now().timestamp()
        result: any = await func(*args, **kwargs)
        end_time: float = datetime.now().timestamp()
        print(f'Function {func.__name__} executed in {end_time - start_time} seconds.')
        return result

    return wrapper


__all__ = ["TOKEN", "timer", "LRUDict"]
