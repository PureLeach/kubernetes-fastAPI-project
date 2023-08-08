import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_liveness_probe(client):
    """Checking the GET /probes/liveness request for k8s"""

    response = client.get('/probes/liveness')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'healthy': True, 'checks': []}


@pytest.mark.asyncio
async def test_readiness_probe(client):
    """Checking GET request /probes/readiness for k8s"""

    response = client.get('/probes/readiness')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'healthy': True, 'checks': []}
