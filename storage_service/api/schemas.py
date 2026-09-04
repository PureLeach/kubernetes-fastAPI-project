"""Pydantic models for the public HTTP API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from storage_service.services.storage import JsonObject

__all__ = ['ErrorBody', 'ErrorResponse', 'JsonObject']


class ErrorBody(BaseModel):
    code: str = Field(..., examples=['not_found'])
    message: str = Field(..., examples=['Object not found'])
    request_id: str | None = Field(default=None, examples=['8e7c9f6a-4d57-4e8b-bd0c-72b2c3a1c1e8'])


class ErrorResponse(BaseModel):
    error: ErrorBody
