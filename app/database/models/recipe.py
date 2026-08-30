from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.category import Category
    from app.database.models.favorite import Favorite
    from app.database.models.ingredient import Ingredient


class Recipe(Base, TimestampMixin):
    __tablename__: str = "recipes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title_en: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    title_ru: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    prep_time_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    instructions_en: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    instructions_ru: Mapped[str] = mapped_column(
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

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="recipes",
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
