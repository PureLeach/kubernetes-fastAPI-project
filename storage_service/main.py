import uvicorn
from fastapi import FastAPI

from storage_service.api import endpoints
from storage_service.core.settings import (
    SERVER_HOST,
    SERVER_PORT,
    SERVER_RELOAD,
)

app = FastAPI()
app.include_router(endpoints.router)


def start():
    """Launched with `poetry run start` at root level"""
    uvicorn.run("storage_service.main:app", host=SERVER_HOST, port=SERVER_PORT, reload=SERVER_RELOAD)
