from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_multilingual_jsonb_and_trgm"
down_revision: str | None = "0001_initial_schema"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    op.add_column(
        "categories",
        sa.Column("name", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(
        "UPDATE categories SET name = jsonb_build_object('en', name_en, 'ru', name_ru) WHERE name IS NULL;",
    )
    op.alter_column("categories", "name", nullable=False)
    op.drop_column("categories", "name_en")
    op.drop_column("categories", "name_ru")

    op.drop_index("ix_recipes_title_en", table_name="recipes")
    op.drop_index("ix_recipes_title_ru", table_name="recipes")
    op.add_column(
        "recipes",
        sa.Column("title", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "recipes",
        sa.Column("instructions", sa.Text(), nullable=True),
    )
    op.execute(
        "UPDATE recipes SET title = jsonb_build_object('en', title_en, 'ru', title_ru) WHERE title IS NULL;",
    )
    op.execute(
        "UPDATE recipes SET instructions = COALESCE(instructions_en, instructions_ru, '') WHERE instructions IS NULL;",
    )
    op.alter_column("recipes", "title", nullable=False)
    op.alter_column("recipes", "instructions", nullable=False)
    op.drop_column("recipes", "title_en")
    op.drop_column("recipes", "title_ru")
    op.drop_column("recipes", "instructions_en")
    op.drop_column("recipes", "instructions_ru")

    op.execute(
        "CREATE INDEX idx_recipes_title_en_trgm ON recipes USING gin ((title->>'en') gin_trgm_ops);",
    )
    op.execute(
        "CREATE INDEX idx_recipes_title_ru_trgm ON recipes USING gin ((title->>'ru') gin_trgm_ops);",
    )
    op.execute(
        "CREATE INDEX idx_recipes_title_es_trgm ON recipes USING gin ((title->>'es') gin_trgm_ops);",
    )

    op.drop_index(
        "ix_ingredients_normalized_name_en",
        table_name="ingredients",
    )
    op.drop_index(
        "ix_ingredients_normalized_name_ru",
        table_name="ingredients",
    )
    op.add_column(
        "ingredients",
        sa.Column("name", sa.String(length=150), nullable=True),
    )
    op.add_column(
        "ingredients",
        sa.Column("normalized_name", sa.String(length=150), nullable=True),
    )
    op.execute(
        "UPDATE ingredients SET name = COALESCE(name_en, name_ru, '') WHERE name IS NULL;",
    )
    op.execute(
        "UPDATE ingredients SET normalized_name = COALESCE(normalized_name_en, normalized_name_ru, '') WHERE normalized_name IS NULL;",
    )
    op.alter_column("ingredients", "name", nullable=False)
    op.alter_column("ingredients", "normalized_name", nullable=False)
    op.drop_column("ingredients", "name_en")
    op.drop_column("ingredients", "name_ru")
    op.drop_column("ingredients", "normalized_name_en")
    op.drop_column("ingredients", "normalized_name_ru")

    op.create_index(
        "ix_ingredients_normalized_name",
        "ingredients",
        ["normalized_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ingredients_normalized_name", table_name="ingredients")
    op.add_column(
        "ingredients",
        sa.Column(
            "normalized_name_ru",
            sa.VARCHAR(length=150),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "ingredients",
        sa.Column(
            "normalized_name_en",
            sa.VARCHAR(length=150),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "ingredients",
        sa.Column(
            "name_ru",
            sa.VARCHAR(length=150),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "ingredients",
        sa.Column(
            "name_en",
            sa.VARCHAR(length=150),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE ingredients SET name_en = name, name_ru = name, normalized_name_en = normalized_name, normalized_name_ru = normalized_name;",
    )
    op.alter_column("ingredients", "name_en", nullable=False)
    op.alter_column("ingredients", "name_ru", nullable=False)
    op.alter_column("ingredients", "normalized_name_en", nullable=False)
    op.alter_column("ingredients", "normalized_name_ru", nullable=False)
    op.drop_column("ingredients", "normalized_name")
    op.drop_column("ingredients", "name")
    op.create_index(
        "ix_ingredients_normalized_name_ru",
        "ingredients",
        ["normalized_name_ru"],
        unique=False,
    )
    op.create_index(
        "ix_ingredients_normalized_name_en",
        "ingredients",
        ["normalized_name_en"],
        unique=False,
    )

    op.execute("DROP INDEX IF EXISTS idx_recipes_title_es_trgm;")
    op.execute("DROP INDEX IF EXISTS idx_recipes_title_ru_trgm;")
    op.execute("DROP INDEX IF EXISTS idx_recipes_title_en_trgm;")
    op.add_column(
        "recipes",
        sa.Column("instructions_ru", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "recipes",
        sa.Column("instructions_en", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "recipes",
        sa.Column(
            "title_ru",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "recipes",
        sa.Column(
            "title_en",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE recipes SET title_en = COALESCE(title->>'en', title->>'ru', ''), title_ru = COALESCE(title->>'ru', title->>'en', ''), instructions_en = instructions, instructions_ru = instructions;",
    )
    op.alter_column("recipes", "title_en", nullable=False)
    op.alter_column("recipes", "title_ru", nullable=False)
    op.alter_column("recipes", "instructions_en", nullable=False)
    op.alter_column("recipes", "instructions_ru", nullable=False)
    op.drop_column("recipes", "instructions")
    op.drop_column("recipes", "title")
    op.create_index(
        "ix_recipes_title_ru",
        "recipes",
        ["title_ru"],
        unique=False,
    )
    op.create_index(
        "ix_recipes_title_en",
        "recipes",
        ["title_en"],
        unique=False,
    )

    op.add_column(
        "categories",
        sa.Column(
            "name_ru",
            sa.VARCHAR(length=100),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "categories",
        sa.Column(
            "name_en",
            sa.VARCHAR(length=100),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE categories SET name_en = COALESCE(name->>'en', name->>'ru', ''), name_ru = COALESCE(name->>'ru', name->>'en', '');",
    )
    op.alter_column("categories", "name_en", nullable=False)
    op.alter_column("categories", "name_ru", nullable=False)
    op.drop_column("categories", "name")

    op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
