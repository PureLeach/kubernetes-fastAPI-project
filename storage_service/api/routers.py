from typing import Any

from fastapi import APIRouter, Header, HTTPException, Response, status
from structlog import getLogger

from storage_service.settings.core import cache, cache_meta

logger = getLogger(__name__)
objects_router = APIRouter(prefix='/objects', tags=['objects'])


@objects_router.put(
    '/{key}',
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary='Запись объекта в хранилище',
)
async def set_object(key: str, json_object: dict[str, Any], expires: int = Header(None)):
    """
    Запись объекта в хранилище

    Args:
        key (str): идентификатор json-объекта в хранилище
        json_object (Dict[str, Any]): сохраняемый json-объект
        expires (int, optional): опциональный заголовок, который определяет ttl объекта в секундах
    """

    await cache.set(key, json_object, ttl=expires)
    cache_meta[key] = expires
    return Response(status_code=status.HTTP_201_CREATED)


@objects_router.get('/{key}', response_model=dict[str, Any], summary='Чтение объекта из хранилища')
async def get_object(key: str):
    """
    Чтение объекта из хранилища

    Args:
        key (str): идентификатор json-объекта в хранилище
    """

    result = await cache.get(key)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Объект не найден')
    return result
