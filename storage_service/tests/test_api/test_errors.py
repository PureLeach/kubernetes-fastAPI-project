"""Every failure leaves through the same envelope."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import status
from fastapi.testclient import TestClient

from storage_service.main import create_app
from storage_service.services.storage import JsonObjectStorage

if TYPE_CHECKING:
    from storage_service.settings.core import Settings


def test_unhandled_exception_becomes_a_structured_500(settings: Settings):
    """An endpoint that blows up returns the envelope, not a stack trace."""
    app = create_app(settings=settings, storage=JsonObjectStorage())

    @app.get('/boom')
    async def boom() -> None:
        raise RuntimeError('kaboom')

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get('/boom', headers={'X-Request-ID': 'trace-me'})

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = response.json()
    assert body['error'] == {
        'code': 'internal_error',
        'message': 'Internal server error.',
        'request_id': 'trace-me',
    }
    assert 'kaboom' not in response.text, 'internal detail must not leak to the client'


def test_validation_error_carries_details(client: TestClient):
    """422 responses keep the field-level detail under `error.details`."""
    response = client.put('/v1/objects/k', json='a bare string')

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    body = response.json()
    assert body['error']['code'] == 'unprocessable_entity'
    assert isinstance(body['error']['details'], list)


def test_unmapped_status_falls_back_to_a_generic_code(settings: Settings):
    """A status without a dedicated code still produces a well-formed envelope."""
    from fastapi import HTTPException

    app = create_app(settings=settings, storage=JsonObjectStorage())

    @app.get('/teapot')
    async def teapot() -> None:
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT, detail='no coffee')

    with TestClient(app) as client:
        response = client.get('/teapot')

    assert response.status_code == status.HTTP_418_IM_A_TEAPOT
    assert response.json()['error']['code'] == 'http_error'
