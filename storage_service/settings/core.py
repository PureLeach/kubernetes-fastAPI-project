"""Application settings, validated with pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """All runtime configuration. Values come from env vars or `.env`."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )

    server_host: str = Field(default='0.0.0.0')
    server_port: int = Field(default=8000, ge=1, le=65535)
    server_reload: bool = Field(default=False)

    log_level_root: str = Field(default='INFO')

    enable_metrics: bool = Field(default=True)

    objects_data_path: Path = Field(default=BASE_DIR.parent / 'mnt' / 'data.json')

    max_object_bytes: int = Field(default=1_048_576, ge=1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
