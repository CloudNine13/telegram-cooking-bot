from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, TimestampMixin


class FridgeItem(Base, TimestampMixin):
    __tablename__: str = "fridge_items"
    __table_args__ = (
        UniqueConstraint(
            "normalized_name",
            name="uq_fridge_items_normalized_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    raw_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    normalized_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )
