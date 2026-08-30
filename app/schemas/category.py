from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name_en: str = Field(min_length=1, max_length=100)
    name_ru: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100)
    parent_id: int | None = Field(default=None)
    order_index: int = Field(default=0)


class CategoryUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name_en: str | None = Field(default=None, min_length=1, max_length=100)
    name_ru: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: int | None = Field(default=None)
    order_index: int | None = Field(default=None)


class CategoryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None = None
    name_en: str
    name_ru: str
    slug: str
    order_index: int = 0
    subcategories: list["CategoryDTO"] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


CategoryDTO.model_rebuild()
