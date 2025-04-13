import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TOKEN = os.getenv("TOKEN")


def timer(func):
    async def wrapper(*args, **kwargs):
        start_time: float = datetime.now().timestamp()
        result: any = await func(*args, **kwargs)
        end_time: float = datetime.now().timestamp()
        print(f'Function {func.__name__} executed in {end_time - start_time} seconds.')
        return result

    return wrapper


__all__ = ["TOKEN", "timer"]
