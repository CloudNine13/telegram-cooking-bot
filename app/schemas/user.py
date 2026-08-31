from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreateOrUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: int
    username: str | None = Field(default=None, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    language_code: str = Field(default="en", min_length=2, max_length=10)


class UserDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str | None = None
    full_name: str
    language_code: str = "en"
    created_at: datetime | None = None
    updated_at: datetime | None = None
