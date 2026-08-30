from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.recipe import Recipe


class Ingredient(Base, TimestampMixin):
    __tablename__: str = "ingredients"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    recipe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    normalized_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )
    quantity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="ingredients",
    )
