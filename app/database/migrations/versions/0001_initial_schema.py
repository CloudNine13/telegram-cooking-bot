from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column(
            "language_code",
            sa.String(length=10),
            server_default="en",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name_en", sa.String(length=100), nullable=False),
        sa.Column("name_ru", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column(
            "order_index",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_categories_parent_id",
        "categories",
        ["parent_id"],
        unique=False,
    )
    op.create_index(
        "ix_categories_slug",
        "categories",
        ["slug"],
        unique=True,
    )

    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("title_en", sa.String(length=255), nullable=False),
        sa.Column("title_ru", sa.String(length=255), nullable=False),
        sa.Column(
            "prep_time_minutes",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("instructions_en", sa.Text(), nullable=False),
        sa.Column("instructions_ru", sa.Text(), nullable=False),
        sa.Column("photo_file_id", sa.String(length=255), nullable=True),
        sa.Column("video_file_id", sa.String(length=255), nullable=True),
        sa.Column("document_file_id", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("instagram_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recipes_category_id",
        "recipes",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        "ix_recipes_title_en",
        "recipes",
        ["title_en"],
        unique=False,
    )
    op.create_index(
        "ix_recipes_title_ru",
        "recipes",
        ["title_ru"],
        unique=False,
    )

    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("name_en", sa.String(length=150), nullable=False),
        sa.Column("name_ru", sa.String(length=150), nullable=False),
        sa.Column("normalized_name_en", sa.String(length=150), nullable=False),
        sa.Column("normalized_name_ru", sa.String(length=150), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingredients_recipe_id",
        "ingredients",
        ["recipe_id"],
        unique=False,
    )
    op.create_index(
        "ix_ingredients_normalized_name_en",
        "ingredients",
        ["normalized_name_en"],
        unique=False,
    )
    op.create_index(
        "ix_ingredients_normalized_name_ru",
        "ingredients",
        ["normalized_name_ru"],
        unique=False,
    )

    op.create_table(
        "fridge_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("raw_name", sa.String(length=150), nullable=False),
        sa.Column("normalized_name", sa.String(length=150), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fridge_items_user_id",
        "fridge_items",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_fridge_items_normalized_name",
        "fridge_items",
        ["normalized_name"],
        unique=False,
    )

    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "recipe_id",
            name="uq_user_recipe_favorite",
        ),
    )
    op.create_index(
        "ix_favorites_user_id",
        "favorites",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_favorites_recipe_id",
        "favorites",
        ["recipe_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_favorites_recipe_id", table_name="favorites")
    op.drop_index("ix_favorites_user_id", table_name="favorites")
    op.drop_table("favorites")

    op.drop_index("ix_fridge_items_normalized_name", table_name="fridge_items")
    op.drop_index("ix_fridge_items_user_id", table_name="fridge_items")
    op.drop_table("fridge_items")

    op.drop_index(
        "ix_ingredients_normalized_name_ru",
        table_name="ingredients",
    )
    op.drop_index(
        "ix_ingredients_normalized_name_en",
        table_name="ingredients",
    )
    op.drop_index("ix_ingredients_recipe_id", table_name="ingredients")
    op.drop_table("ingredients")

    op.drop_index("ix_recipes_title_ru", table_name="recipes")
    op.drop_index("ix_recipes_title_en", table_name="recipes")
    op.drop_index("ix_recipes_category_id", table_name="recipes")
    op.drop_table("recipes")

    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_table("categories")

    op.drop_table("users")
