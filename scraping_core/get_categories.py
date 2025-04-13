import json
import aiohttp
import asyncio
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from config import timer

user = UserAgent()


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url=url, headers={"user-agent": f"{user.random}"}) as response:
        return await response.text()


# Функция для получения статуса ответа от сервера
async def response_status(session: aiohttp.ClientSession, url: str) -> int | None:
    try:
        async with session.get(url=url, headers={"user-agent": f"{user.random}"}) as response:
            return response.status
    except aiohttp.ClientError:
        return None


# Функция для проверки одной страницы с использованием семафора
async def check_page(session, url, page, sem):
    async with sem:
        status = await response_status(session, url)
        if status is not None and status != 404:
            name = await get_category_name(content=await fetch(session, url))
            if name:
                return {page: name}
        return None


async def get_category_name(content) -> str:
    soup = BeautifulSoup(content, "lxml")
    return str(soup.find("h1").text)


# Основная функция для проверки множества страниц
async def get_categories_count(domen_url: str, max_pages: int = 4000,
                               concurrency: int = 500) -> dict:
    real_pages: dict = {}
    sem = asyncio.Semaphore(concurrency)  # Ограничение на одновременные запросы
    async with aiohttp.ClientSession() as session:
        tasks = []
        for page in range(max_pages):
            url = f"{domen_url.rstrip('/')}/{page}"
            task = asyncio.create_task(check_page(session, url, page, sem))
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        for result in results:
            result: dict
            if result is not None and result.values():
                real_pages |= result
    return real_pages


@timer
async def main():
    url = "https://www.labirint.ru/genres/"
    real_pages: dict = await get_categories_count(domen_url=url)
    with open("categories.json", "w", encoding="utf-8") as file:
        json.dump(real_pages, file, indent=4, ensure_ascii=False)
    print("Доступные страницы:", real_pages)


if __name__ == "__main__":
    asyncio.run(main())
