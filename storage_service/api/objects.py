from typing import Any

from fastapi import APIRouter, Header, HTTPException, Response, status
from structlog import getLogger

from storage_service.services.storage import storage

logger = getLogger(__name__)
objects_router = APIRouter(prefix='/objects', tags=['objects'])


@objects_router.put(
    '/{key}',
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary='Writing an object to the storage',
)
async def set_object(
    key: str,
    json_object: dict[str, Any],
    expires: int | None = Header(default=None),
) -> Response:
    """
    Writing an object to the storage.

    Args:
        key: identifier of the json object in the storage
        json_object: stored json object
        expires: optional header that specifies the object's TTL in seconds; absent → no expiry
    """
    await storage.set(key, json_object, ttl=expires)
    return Response(status_code=status.HTTP_201_CREATED)


@objects_router.get(
    '/{key}',
    response_model=dict[str, Any],
    summary='Reading an object from storage',
)
async def get_object(key: str) -> dict[str, Any]:
    """
    Reading an object from storage.

    Args:
        key: identifier of the json object in the storage
    """
    result = await storage.get(key)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Object not found')
    return result
