import os
from datetime import datetime
import aiohttp
from dotenv import load_dotenv, find_dotenv
from fake_useragent import UserAgent

load_dotenv(find_dotenv())

TOKEN = os.getenv("TOKEN")
user = UserAgent()


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url=url, headers={"user-agent": f"{user.random}"}) as response:
        return await response.text()


# Функция для получения статуса ответа от сервера
async def get_response_status(session: aiohttp.ClientSession, url: str) -> int | None:
    try:
        async with session.get(url=url, headers={"user-agent": f"{user.random}"}) as response:
            return response.status
    except aiohttp.ClientError:
        return None


def timer(func):
    async def wrapper(*args, **kwargs):
        start_time: float = datetime.now().timestamp()
        result: any = await func(*args, **kwargs)
        end_time: float = datetime.now().timestamp()
        print(f'Function {func.__name__} executed in {end_time - start_time} seconds.')
        return result

    return wrapper


__all__ = ["TOKEN", "timer", "fetch", "get_response_status"]
