import re

import pytest

UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


@pytest.mark.asyncio
async def test_generates_request_id_when_missing(client):
    """The middleware echoes a generated UUID when no header is supplied."""
    response = client.get('/v1/objects/missing')
    request_id = response.headers.get('X-Request-ID')
    assert request_id and UUID_RE.match(request_id)


@pytest.mark.asyncio
async def test_propagates_inbound_request_id(client):
    """An inbound X-Request-ID header is preserved on the response and in error bodies."""
    inbound = 'fixed-id-123'
    response = client.get('/v1/objects/missing', headers={'X-Request-ID': inbound})
    assert response.headers['X-Request-ID'] == inbound
    assert response.json()['error']['request_id'] == inbound
