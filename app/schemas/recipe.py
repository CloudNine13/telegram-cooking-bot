from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryDTO


class IngredientCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name_en: str = Field(min_length=1, max_length=150)
    name_ru: str = Field(min_length=1, max_length=150)
    normalized_name_en: str | None = Field(default=None, max_length=150)
    normalized_name_ru: str | None = Field(default=None, max_length=150)
    quantity: float | None = Field(default=None, ge=0.0)
    unit: str | None = Field(default=None, max_length=50)


class IngredientDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int
    name_en: str
    name_ru: str
    normalized_name_en: str
    normalized_name_ru: str
    quantity: float | None = None
    unit: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RecipeCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category_id: int
    title_en: str = Field(min_length=1, max_length=255)
    title_ru: str = Field(min_length=1, max_length=255)
    prep_time_minutes: int = Field(default=0, ge=0)
    instructions_en: str = Field(min_length=1)
    instructions_ru: str = Field(min_length=1)
    photo_file_id: str | None = Field(default=None, max_length=255)
    video_file_id: str | None = Field(default=None, max_length=255)
    document_file_id: str | None = Field(default=None, max_length=255)
    source_url: str | None = Field(default=None, max_length=1024)
    instagram_url: str | None = Field(default=None, max_length=1024)
    ingredients: list[IngredientCreateDTO] = Field(default_factory=list)


class RecipeUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category_id: int | None = Field(default=None)
    title_en: str | None = Field(default=None, min_length=1, max_length=255)
    title_ru: str | None = Field(default=None, min_length=1, max_length=255)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    instructions_en: str | None = Field(default=None, min_length=1)
    instructions_ru: str | None = Field(default=None, min_length=1)
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
    title_en: str
    title_ru: str
    prep_time_minutes: int = 0
    instructions_en: str
    instructions_ru: str
    photo_file_id: str | None = None
    video_file_id: str | None = None
    document_file_id: str | None = None
    source_url: str | None = None
    instagram_url: str | None = None
    category: CategoryDTO | None = None
    ingredients: list[IngredientDTO] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ParsedRecipeTemplateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title_en: str | None = Field(default=None, max_length=255)
    title_ru: str | None = Field(default=None, max_length=255)
    category_slug: str | None = Field(default=None, max_length=100)
    prep_time_minutes: int = Field(default=0, ge=0)
    instructions_en: str | None = Field(default=None)
    instructions_ru: str | None = Field(default=None)
    source_url: str | None = Field(default=None, max_length=1024)
    instagram_url: str | None = Field(default=None, max_length=1024)
    ingredients: list[IngredientCreateDTO] = Field(default_factory=list)
