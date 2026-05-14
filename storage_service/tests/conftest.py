import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from storage_service.main import app
from storage_service.services.storage import storage


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest_asyncio.fixture(autouse=True)
async def _clean_storage():
    """Reset the in-memory storage between tests."""
    yield
    await storage.clear()
