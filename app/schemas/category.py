from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CategoryCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: dict[str, str] = Field(min_length=1)
    slug: str = Field(min_length=1, max_length=100)
    parent_id: int | None = Field(default=None)
    order_index: int = Field(default=0)


class CategoryUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: dict[str, str] | None = Field(default=None)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: int | None = Field(default=None)
    order_index: int | None = Field(default=None)


class CategoryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None = None
    name: dict[str, str]
    slug: str
    order_index: int = 0
    subcategories: list["CategoryDTO"] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def extract_from_orm(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        if hasattr(data, "__dict__"):
            subcats = data.__dict__.get("subcategories", [])
            return {
                "id": getattr(data, "id", None),
                "parent_id": getattr(data, "parent_id", None),
                "name": getattr(data, "name", {}),
                "slug": getattr(data, "slug", None),
                "order_index": getattr(data, "order_index", 0),
                "subcategories": subcats if subcats is not None else [],
                "created_at": getattr(data, "created_at", None),
                "updated_at": getattr(data, "updated_at", None),
            }

        return data


CategoryDTO.model_rebuild()
