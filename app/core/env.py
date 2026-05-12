from functools import lru_cache

from dotenv import load_dotenv


@lru_cache
def load_environment() -> None:
    load_dotenv()
