"""End-to-end tests for the /v1/objects endpoints."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from fastapi import status

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from storage_service.services.storage import JsonObjectStorage


def test_set_object(client: TestClient):
    """PUT /v1/objects/{key} stores the payload and reports 201."""
    response = client.put('/v1/objects/widget-42', json={'name': 'widget'}, headers={'expires': '600'})

    assert response.status_code == status.HTTP_201_CREATED
    assert client.get('/v1/objects/widget-42').json() == {'name': 'widget'}


def test_set_object_without_expires_stores_it_indefinitely(client: TestClient):
    """The `expires` header is optional; omitting it means no expiry."""
    assert client.put('/v1/objects/forever', json={'v': 1}).status_code == status.HTTP_201_CREATED
    assert client.get('/v1/objects/forever').status_code == status.HTTP_200_OK


def test_set_object_overwrites_an_existing_key(client: TestClient):
    """A second PUT to the same key replaces the stored value."""
    client.put('/v1/objects/dup', json={'version': 1})
    client.put('/v1/objects/dup', json={'version': 2})

    assert client.get('/v1/objects/dup').json() == {'version': 2}


def test_get_object_not_found(client: TestClient):
    """GET /v1/objects/{key} returns the unified error envelope on 404."""
    response = client.get('/v1/objects/nonexistent')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body['error']['code'] == 'not_found'
    assert body['error']['message'] == 'Object not found'
    assert body['error']['request_id']


@pytest.mark.parametrize(
    'expires',
    [
        pytest.param('0', id='zero'),
        pytest.param('-1', id='negative'),
        pytest.param('not-a-number', id='not-a-number'),
    ],
)
def test_rejects_an_invalid_expires_header(client: TestClient, expires: str):
    """A nonsensical TTL is refused up front rather than passed to the cache."""
    response = client.put('/v1/objects/k', json={'v': 1}, headers={'expires': expires})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()['error']['code'] == 'unprocessable_entity'


@pytest.mark.parametrize(
    'key',
    [
        pytest.param('spaces are not allowed', id='whitespace'),
        pytest.param('key$with!chars', id='punctuation'),
        pytest.param('x' * 300, id='too-long'),
    ],
)
def test_rejects_an_invalid_key(client: TestClient, key: str):
    """Keys reach the logs and the snapshot file, so they are constrained."""
    assert client.put(f'/v1/objects/{key}', json={'v': 1}).status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)


def test_rejects_a_non_object_body(client: TestClient):
    """The endpoint stores JSON objects; a bare array is a validation error."""
    response = client.put('/v1/objects/k', json=[1, 2, 3])

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()['error']['details']


@pytest.mark.asyncio
async def test_expired_object_is_no_longer_readable(
    client: TestClient,
    storage: JsonObjectStorage,
):
    """Once the deadline passes the object is gone, even before eviction runs."""
    client.put('/v1/objects/short', json={'v': 1}, headers={'expires': '60'})
    storage._expires_at['short'] = time.time() - 1  # noqa: SLF001

    assert client.get('/v1/objects/short').status_code == status.HTTP_404_NOT_FOUND
