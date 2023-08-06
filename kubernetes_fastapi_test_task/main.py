import uvicorn
from fastapi import FastAPI

from kubernetes_fastapi_test_task.api import endpoints
from kubernetes_fastapi_test_task.core.settings import SERVER_HOST, SERVER_PORT, SERVER_RELOAD

app = FastAPI()
app.include_router(endpoints.router)


if __name__ == '__main__':
    uvicorn.run('main:app', host=SERVER_HOST, port=SERVER_PORT, reload=SERVER_RELOAD)
