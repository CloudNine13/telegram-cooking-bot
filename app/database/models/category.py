from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.recipe import Recipe


class Category(Base, TimestampMixin):
    __tablename__: str = "categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    name_ru: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    parent: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="subcategories",
        remote_side="Category.id",
    )
    subcategories: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="Category.order_index",
    )
    recipes: Mapped[list["Recipe"]] = relationship(
        "Recipe",
        back_populates="category",
        cascade="all, delete-orphan",
    )
