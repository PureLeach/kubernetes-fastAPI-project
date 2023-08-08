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
    summary='Writing an object to the storage',
)
async def set_object(key: str, json_object: dict[str, Any], expires: int = Header(None)):
    """
    Writing an object to the storage

    Args:
        key (str): identifier of the json object in the storage
        json_object (Dict[str, Any]): stored json object
        expires (int, optional): optional header that specifies the object's ttl in seconds
    """

    await cache.set(key, json_object, ttl=expires)
    cache_meta[key] = expires
    return Response(status_code=status.HTTP_201_CREATED)


@objects_router.get('/{key}', response_model=dict[str, Any], summary='Reading an object from storage')
async def get_object(key: str):
    """
    Reading an object from storage

    Args:
        key (str): identifier of the json object in the storage
    """

    result = await cache.get(key)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Object not found')
    return result
