from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.favorite import Favorite
    from app.database.models.fridge import FridgeItem


class User(Base, TimestampMixin):
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )
    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    language_code: Mapped[str] = mapped_column(
        String(10),
        default="en",
        server_default="en",
        nullable=False,
    )

    fridge_items: Mapped[list["FridgeItem"]] = relationship(
        "FridgeItem",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
