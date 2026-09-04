"""X-Request-ID propagation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def test_generates_request_id_when_missing(client: TestClient):
    """The middleware echoes a generated UUID when no header is supplied."""
    request_id = client.get('/v1/objects/missing').headers.get('X-Request-ID')

    assert request_id is not None
    assert UUID_RE.match(request_id)


def test_propagates_inbound_request_id(client: TestClient):
    """An inbound X-Request-ID is preserved on the response and in error bodies."""
    response = client.get('/v1/objects/missing', headers={'X-Request-ID': 'fixed-id-123'})

    assert response.headers['X-Request-ID'] == 'fixed-id-123'
    assert response.json()['error']['request_id'] == 'fixed-id-123'


def test_each_request_gets_its_own_id(client: TestClient):
    """Ids are per-request, not per-process — contextvars must not leak between them."""
    first = client.get('/v1/objects/missing').headers['X-Request-ID']
    second = client.get('/v1/objects/missing').headers['X-Request-ID']

    assert first != second
