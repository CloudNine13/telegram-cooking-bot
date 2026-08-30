from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recipe import RecipeDTO


class FridgeItemCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    raw_name: str = Field(min_length=1, max_length=150)
    normalized_name: str | None = Field(default=None, max_length=150)


class FridgeItemDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_name: str
    normalized_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RecipeMatchResultDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recipe: RecipeDTO
    match_type: Literal["full", "partial"] = "full"
    matched_count: int = 0
    missing_count: int = 0
    matched_ingredients: list[str] = Field(default_factory=list)
    missing_ingredients: list[str] = Field(default_factory=list)
    match_percentage: float = 0.0
    is_full_match: bool = False
