from aiogram import Bot, Dispatcher
import asyncio
from config import TOKEN
from app.handlers import router


async def main():
    if not TOKEN:
        raise ValueError("You must provide a token before creating a new instance of the bot.")
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router=router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        print("Start polling...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stop polling.")
        exit(1)
