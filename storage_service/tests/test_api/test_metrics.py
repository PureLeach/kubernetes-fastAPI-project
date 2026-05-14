import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_metrics(client):
    """GET /metrics returns a Prometheus exposition payload."""
    response = client.get('/metrics')

    assert response.status_code == status.HTTP_200_OK
    assert response.headers['content-type'].startswith('text/plain')
    assert b'# HELP' in response.content
