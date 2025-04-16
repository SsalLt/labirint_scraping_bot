import asyncio

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

user = UserAgent()


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url=url, headers={"user-agent": f"{user.random}"}) as response:
        return await response.text()


async def get_response_status(session: aiohttp.ClientSession, url: str) -> int | None:
    try:
        async with session.get(url=url, headers={"user-agent": f"{user.random}"}) as response:
            return response.status
    except aiohttp.ClientError:
        return None


async def get_category_name(session: aiohttp.ClientSession, url: str, page: int,
                            sem: asyncio.Semaphore) -> dict[int: str] | None:
    async def scrap_category_name(content: str) -> str:
        soup = BeautifulSoup(content, "lxml")
        h1 = soup.find("h1")
        return h1.text.strip() if h1 else None

    async with sem:
        status = await get_response_status(session, url)
        if status is not None and status != 404:
            name = await scrap_category_name(content=await fetch(session, url))
            if name:
                return {page: name}
        return None


__all__ = ['fetch', 'get_response_status', 'get_category_name']
