"""HTTP endpoints for the object storage."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Response, status
from structlog import getLogger

from storage_service.api.dependencies import enforce_payload_limit, get_storage
from storage_service.api.schemas import ErrorResponse, JsonObject
from storage_service.services.storage import JsonObjectStorage  # noqa: TC001 — runtime needed by FastAPI DI

logger = getLogger(__name__)
objects_router = APIRouter(prefix='/objects', tags=['objects'])


_OBJECT_EXAMPLE = {'name': 'widget', 'qty': 12, 'tags': ['a', 'b']}


@objects_router.put(
    '/{key}',
    status_code=status.HTTP_201_CREATED,
    summary='Store a JSON object',
    dependencies=[Depends(enforce_payload_limit)],
    responses={
        status.HTTP_201_CREATED: {'description': 'Object stored.'},
        status.HTTP_413_CONTENT_TOO_LARGE: {
            'model': ErrorResponse,
            'description': 'Payload exceeds max_object_bytes.',
        },
    },
)
async def set_object(
    key: str,
    json_object: Annotated[
        JsonObject,
        Body(description='Arbitrary JSON object to store.', examples=[_OBJECT_EXAMPLE]),
    ],
    storage: Annotated[JsonObjectStorage, Depends(get_storage)],
    expires: Annotated[int | None, Header(description='TTL in seconds. Absent → no expiry.')] = None,
) -> Response:
    """Store `json_object` under `key`. Existing values are overwritten."""
    await storage.set(key, json_object, ttl=expires)
    logger.info('object_set', key=key, ttl=expires)
    return Response(status_code=status.HTTP_201_CREATED)


@objects_router.get(
    '/{key}',
    summary='Read a JSON object',
    response_model=JsonObject,
    responses={
        status.HTTP_200_OK: {'content': {'application/json': {'example': _OBJECT_EXAMPLE}}},
        status.HTTP_404_NOT_FOUND: {'model': ErrorResponse, 'description': 'Object not found.'},
    },
)
async def get_object(
    key: str,
    storage: Annotated[JsonObjectStorage, Depends(get_storage)],
) -> JsonObject:
    """Return the object stored under `key`, or 404 if missing/expired."""
    result = await storage.get(key)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Object not found')
    return result
