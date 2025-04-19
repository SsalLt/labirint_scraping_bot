import aiohttp
import asyncio
import bs4
from scraping_core.scraping_functions import get_response_status, fetch


def safe_extract(func, default=None):
    try:
        return func() or default
    except (AttributeError, ValueError):
        return default


def scrap_item(item: bs4.element.Tag) -> dict:
    item_name: str | None = safe_extract(lambda: item.find(class_='product need-watch').attrs.get('data-name').strip())
    item_author: str | None = safe_extract(lambda: item.find(class_='product-author').find('a').text.strip())
    pubhouse_elements: str | None = safe_extract(
        lambda: [pbh.text.strip() for pbh in item.find(class_='product-pubhouse').find_all('a')], default=[])
    item_pubhouse: str = ': '.join(pubhouse_elements) if pubhouse_elements else 'Не указано'

    discounted_price: int | None = safe_extract(lambda: int(
        item.find(class_='product-cover').find('span', class_='price-val').find('span').text.replace(' ', '')))
    old_price: int | None = safe_extract(lambda: int(
        item.find(class_='product-cover').find('span', class_='price-old').find('span').text.replace(' ', '')))
    item_sale: int | None = round(
        ((old_price - discounted_price) / old_price) * 100) if discounted_price and old_price else None
    item_link: str | None = safe_extract(lambda: f"https://www.labirint.ru"
                                                 f"{item.find(class_='product-cover').find('a').attrs.get('href')}")

    return {
        'book_title': item_name,
        'book_link': item_link,
        'book_author': item_author,
        'book_publishing': item_pubhouse,
        'book_discounted_price': discounted_price,
        'book_old_price': old_price,
        'book_sale': item_sale
    }


async def collect_data(genre: int) -> tuple[str, list[dict]] | None:
    data: list = []

    async with (aiohttp.ClientSession() as session):
        initial_url: str = f'https://www.labirint.ru/genres/{genre}/?available=1&paperbooks=1'
        status = await get_response_status(session, initial_url)
        if not str(status).startswith("2"):
            return None
        response: str = await fetch(session, initial_url)
        soup = bs4.BeautifulSoup(response, 'lxml')
        category_name: str = soup.find("h1").text.strip()
        print(category_name)
        pages_numbers = soup.find_all('div', class_='pagination-number')
        pages_count: int = int(pages_numbers[-1].text.strip()) if pages_numbers else 1

        tasks: list = [fetch(session, f'{initial_url}&page={page}')
                       for page in range(1, pages_count + 1)]
        pages_content = await asyncio.gather(*tasks)

        cnt: int = 0
        for page_content in pages_content:
            soup = bs4.BeautifulSoup(page_content, 'lxml')
            books_items: list = soup.find_all('div', class_='genres-carousel__item')
            for item in books_items:
                item_data: dict = scrap_item(item)
                data.append(item_data)
            cnt += 1
            print(f'Completed {cnt} out of {pages_count}')
    return category_name, data
