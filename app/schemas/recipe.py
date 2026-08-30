from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.category import CategoryDTO


class IngredientCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=150)
    normalized_name: str | None = Field(default=None, max_length=150)
    quantity: float | None = Field(default=None, ge=0.0)
    unit: str | None = Field(default=None, max_length=50)


class IngredientDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int
    name: str
    normalized_name: str
    quantity: float | None = None
    unit: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RecipeCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category_id: int
    title: dict[str, str] = Field(min_length=1)
    prep_time_minutes: int = Field(default=0, ge=0)
    instructions: str = Field(min_length=1)
    photo_file_id: str | None = Field(default=None, max_length=255)
    video_file_id: str | None = Field(default=None, max_length=255)
    document_file_id: str | None = Field(default=None, max_length=255)
    source_url: str | None = Field(default=None, max_length=1024)
    instagram_url: str | None = Field(default=None, max_length=1024)
    ingredients: list[IngredientCreateDTO] = Field(default_factory=list)


class RecipeUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category_id: int | None = Field(default=None)
    title: dict[str, str] | None = Field(default=None)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    instructions: str | None = Field(default=None, min_length=1)
    photo_file_id: str | None = Field(default=None, max_length=255)
    video_file_id: str | None = Field(default=None, max_length=255)
    document_file_id: str | None = Field(default=None, max_length=255)
    source_url: str | None = Field(default=None, max_length=1024)
    instagram_url: str | None = Field(default=None, max_length=1024)
    ingredients: list[IngredientCreateDTO] | None = Field(default=None)


class RecipeDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    title: dict[str, str]
    prep_time_minutes: int = 0
    instructions: str
    photo_file_id: str | None = None
    video_file_id: str | None = None
    document_file_id: str | None = None
    source_url: str | None = None
    instagram_url: str | None = None
    category: CategoryDTO | None = None
    ingredients: list[IngredientDTO] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def extract_from_orm(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        if hasattr(data, "__dict__"):
            cat = data.__dict__.get("category")
            ings = data.__dict__.get("ingredients", [])
            return {
                "id": getattr(data, "id", None),
                "category_id": getattr(data, "category_id", None),
                "title": getattr(data, "title", {}),
                "prep_time_minutes": getattr(data, "prep_time_minutes", 0),
                "instructions": getattr(data, "instructions", ""),
                "photo_file_id": getattr(data, "photo_file_id", None),
                "video_file_id": getattr(data, "video_file_id", None),
                "document_file_id": getattr(data, "document_file_id", None),
                "source_url": getattr(data, "source_url", None),
                "instagram_url": getattr(data, "instagram_url", None),
                "category": cat,
                "ingredients": ings if ings is not None else [],
                "created_at": getattr(data, "created_at", None),
                "updated_at": getattr(data, "updated_at", None),
            }

        return data


class ParsedRecipeTemplateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: dict[str, str] | None = Field(default=None)
    title_en: str | None = Field(default=None, max_length=255)
    title_ru: str | None = Field(default=None, max_length=255)
    category_slug: str | None = Field(default=None, max_length=100)
    prep_time_minutes: int = Field(default=0, ge=0)
    instructions: str | None = Field(default=None)
    instructions_en: str | None = Field(default=None)
    instructions_ru: str | None = Field(default=None)
    source_url: str | None = Field(default=None, max_length=1024)
    instagram_url: str | None = Field(default=None, max_length=1024)
    ingredients: list[IngredientCreateDTO] = Field(default_factory=list)
