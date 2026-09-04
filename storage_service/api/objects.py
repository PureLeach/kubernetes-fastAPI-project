"""HTTP endpoints for the object storage."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Path, Response, status
from structlog import getLogger

from storage_service.api.dependencies import enforce_payload_limit, get_storage
from storage_service.api.schemas import ErrorResponse, JsonObject
from storage_service.services.storage import JsonObjectStorage  # noqa: TC001 — runtime needed by FastAPI DI
from storage_service.settings.core import MAX_TTL_SECONDS

logger = getLogger(__name__)
objects_router = APIRouter(prefix='/objects', tags=['objects'])


_OBJECT_EXAMPLE = {'name': 'widget', 'qty': 12, 'tags': ['a', 'b']}

# Keys reach the logs and the snapshot file, so keep them boring.
_KEY_PATTERN = r'^[A-Za-z0-9._:-]+$'

ObjectKey = Annotated[
    str,
    Path(
        description='Object key. Letters, digits, dot, underscore, colon and dash.',
        pattern=_KEY_PATTERN,
        max_length=256,
        examples=['widget-42'],
    ),
]

Expires = Annotated[
    int | None,
    Header(
        description='TTL in seconds. Absent → no expiry.',
        ge=1,
        le=MAX_TTL_SECONDS,
    ),
]


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
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            'model': ErrorResponse,
            'description': 'Invalid key or `expires` header.',
        },
    },
)
async def set_object(
    key: ObjectKey,
    json_object: Annotated[
        JsonObject,
        Body(description='Arbitrary JSON object to store.', examples=[_OBJECT_EXAMPLE]),
    ],
    storage: Annotated[JsonObjectStorage, Depends(get_storage)],
    expires: Expires = None,
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
    key: ObjectKey,
    storage: Annotated[JsonObjectStorage, Depends(get_storage)],
) -> JsonObject:
    """Return the object stored under `key`, or 404 if missing/expired."""
    result = await storage.get(key)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Object not found')
    return result
