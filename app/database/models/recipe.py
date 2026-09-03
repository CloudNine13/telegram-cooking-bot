from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.category import Category
    from app.database.models.favorite import Favorite
    from app.database.models.ingredient import Ingredient


recipe_categories: Table = Table(
    "recipe_categories",
    Base.metadata,
    Column(
        "recipe_id",
        Integer,
        ForeignKey("recipes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "category_id",
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class Recipe(Base, TimestampMixin):
    __tablename__: str = "recipes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    title: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        nullable=False,
    )
    prep_time_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    instructions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    photo_file_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    video_file_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    document_file_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    source_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
    instagram_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary=recipe_categories,
        back_populates="recipes",
        lazy="selectin",
    )
    ingredients: Mapped[list["Ingredient"]] = relationship(
        "Ingredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )
