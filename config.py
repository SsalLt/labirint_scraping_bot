import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TOKEN = os.getenv("TOKEN")

__all__ = ["TOKEN"]
