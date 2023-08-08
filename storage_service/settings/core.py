"""
Основные настройки и параметры приложения
"""

from pathlib import Path

from aiocache import Cache
from aiocache.serializers import JsonSerializer
from environs import Env

env = Env()
env.read_env(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

SERVER_HOST = env.str('SERVER_HOST', default='0.0.0.0')
SERVER_PORT = env.int('SERVER_PORT', default=8000)
SERVER_RELOAD = env.bool('SERVER_RELOAD', default=True)


cache = Cache(
    Cache.MEMORY,
    serializer=JsonSerializer(),
)
cache_keys: set[str] = set()
