import csv
import json
import aiohttp
import asyncio
from config import timer
from scraping_core.scraping_functions import get_category_name


async def get_categories_count(domen_url: str, max_pages: int = 4000,
                               concurrency: int = 500) -> dict:
    real_pages: dict = {}
    print("Start update categories")
    sem = asyncio.Semaphore(concurrency)  # Ограничение на одновременные запросы
    async with aiohttp.ClientSession() as session:
        tasks: list = []
        for page in range(max_pages):
            url = f"{domen_url.rstrip('/')}/{page}"
            task = asyncio.create_task(get_category_name(session, url, page, sem))
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
    with open("categories.json", "w", encoding="utf-8") as json_file:
        json.dump(real_pages, json_file, indent=4, ensure_ascii=False)

    # Запись в CSV файл
    with open("categories.csv", "w", newline='', encoding="utf-8-sig") as csv_file:
        writer = csv.writer(
            csv_file,
            delimiter=';',
            quoting=csv.QUOTE_ALL
        )
        writer.writerow(["Номер категории", "Название категории"])
        for key, value in real_pages.items():
            writer.writerow([
                int(str(key).replace(';', ',')),
                str(value).replace(';', ',')
            ])

    # Запись в TXT файл
    with open("categories.txt", "w", encoding="utf-8") as txt_file:
        for key, value in real_pages.items():
            txt_file.write(f"{key} - {value}\n")


if __name__ == "__main__":
    asyncio.run(update_categories())
