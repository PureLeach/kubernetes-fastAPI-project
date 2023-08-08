from typing import Any

from fastapi import APIRouter, Header, HTTPException, Response, status
from structlog import getLogger

from storage_service.settings.core import cache, cache_keys

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

    result = await cache.set(key, json_object, ttl=expires)
    if result:
        cache_keys.add(key)
        return Response(status_code=status.HTTP_201_CREATED)
    logger.error('Ошибка при попытке сохранения объекта', key=key, json_object=json_object, expires=expires)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Неопределенная ошибка сервера')


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
