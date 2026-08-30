from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_shared_admin_fridge"
down_revision: str | None = "0002_multilingual_jsonb_and_trgm"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(
        "ix_fridge_items_user_id",
        table_name="fridge_items",
        if_exists=True,
    )
    op.drop_constraint(
        "fridge_items_user_id_fkey",
        "fridge_items",
        type_="foreignkey",
    )
    op.drop_column("fridge_items", "user_id")

    op.add_column(
        "fridge_items",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.drop_index(
        "ix_fridge_items_normalized_name",
        table_name="fridge_items",
        if_exists=True,
    )
    op.create_unique_constraint(
        "uq_fridge_items_normalized_name",
        "fridge_items",
        ["normalized_name"],
    )
    op.create_index(
        "ix_fridge_items_normalized_name",
        "fridge_items",
        ["normalized_name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fridge_items_normalized_name",
        table_name="fridge_items",
        if_exists=True,
    )
    op.drop_constraint(
        "uq_fridge_items_normalized_name",
        "fridge_items",
        type_="unique",
    )
    op.create_index(
        "ix_fridge_items_normalized_name",
        "fridge_items",
        ["normalized_name"],
        unique=False,
    )

    op.drop_column("fridge_items", "updated_at")

    op.add_column(
        "fridge_items",
        sa.Column("user_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fridge_items_user_id_fkey",
        "fridge_items",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_fridge_items_user_id",
        "fridge_items",
        ["user_id"],
        unique=False,
    )
