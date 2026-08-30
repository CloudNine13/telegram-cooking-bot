import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = Field(
        default="",
        validation_alias="TELEGRAM_BOT_TOKEN",
    )
    admin_user_ids: list[int] = Field(
        default_factory=list,
        validation_alias="ADMIN_USER_IDS",
    )
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/cooking_bot",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    default_locale: str = Field(
        default="en",
        validation_alias="DEFAULT_LOCALE",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def parse_admin_user_ids(cls, value: Any) -> list[int]:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []

            if stripped.startswith("[") and stripped.endswith("]"):
                parsed: Any = json.loads(stripped)
                if isinstance(parsed, list):
                    return [int(item) for item in parsed]

            return [int(item.strip()) for item in stripped.split(",") if item.strip()]

        if isinstance(value, (list, tuple, set)):
            return [int(item) for item in value]

        if isinstance(value, int):
            return [value]

        return []


@lru_cache
def get_settings() -> Settings:
    return Settings()
