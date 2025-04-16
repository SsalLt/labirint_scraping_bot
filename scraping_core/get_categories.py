import csv
import json
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from config import timer, get_response_status, fetch


# Функция для проверки одной страницы с использованием семафора
async def check_page(session, url, page, sem):
    async with sem:
        status = await get_response_status(session, url)
        if status is not None and status != 404:
            name = await get_category_name(content=await fetch(session, url))
            if name:
                return {page: name}
        return None


async def get_category_name(content) -> str:
    soup = BeautifulSoup(content, "lxml")
    h1 = soup.find("h1")
    return h1.text.strip() if h1 else None


# Основная функция для проверки множества страниц
async def get_categories_count(domen_url: str, max_pages: int = 4000,
                               concurrency: int = 500) -> dict:
    real_pages: dict = {}
    print("Start update categories")
    sem = asyncio.Semaphore(concurrency)  # Ограничение на одновременные запросы
    async with aiohttp.ClientSession() as session:
        tasks: list = []
        for page in range(max_pages):
            url = f"{domen_url.rstrip('/')}/{page}"
            task = asyncio.create_task(check_page(session, url, page, sem))
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        for result in results:
            result: dict
            if result is not None and result.values():
                real_pages.update(result)
                if len(real_pages) % 100 == 0:
                    print(len(real_pages))
    print("end update categories")
    return real_pages


@timer
async def update_categories():
    url = "https://www.labirint.ru/genres/"
    real_pages: dict = await get_categories_count(domen_url=url)

    # Запись в JSON файл
    with open("scraping_core/categories.json", "w", encoding="utf-8") as json_file:
        json.dump(real_pages, json_file, indent=4, ensure_ascii=False)

    # Запись в CSV файл
    with open("scraping_core/categories.csv", "w", newline='', encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Номер категории", "Название категории"])
        for key, value in real_pages.items():
            writer.writerow([key, value])

    # Запись в TXT файл
    with open("scraping_core/categories.txt", "w", encoding="utf-8") as txt_file:
        for key, value in real_pages.items():
            txt_file.write(f"{key} - {value}\n")


if __name__ == "__main__":
    asyncio.run(update_categories())
