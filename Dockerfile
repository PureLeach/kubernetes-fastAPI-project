FROM python:3.11.1-slim-bullseye AS builder

COPY pyproject.toml poetry.lock ./
RUN python -m pip install --no-cache-dir poetry==1.4.2 \
    && poetry export --without-hashes --without dev,test -f requirements.txt -o requirements.txt


FROM python:3.11.1-slim-bullseye

COPY --from=builder requirements.txt ./
COPY ./storage_service ./storage_service/
COPY .env ./

RUN python -m pip install --no-cache-dir -r requirements.txt
