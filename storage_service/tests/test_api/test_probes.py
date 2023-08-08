import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_liveness_probe(client):
    """Проверка запроса GET /probes/liveness для k8s"""

    response = client.get('/probes/liveness')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'healthy': True, 'checks': []}


@pytest.mark.asyncio
async def test_readiness_probe(client):
    """Проверка запроса GET /probes/readiness для k8s"""

    response = client.get('/probes/readiness')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'healthy': True, 'checks': []}
