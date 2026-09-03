from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_multi_category_recipes"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recipe_categories",
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("recipe_id", "category_id"),
    )
    op.create_index(
        "ix_recipe_categories_category_id",
        "recipe_categories",
        ["category_id"],
        unique=False,
    )

    op.execute(
        sa.text(
            """
            INSERT INTO recipe_categories (recipe_id, category_id)
            SELECT id, category_id FROM recipes WHERE category_id IS NOT NULL
            ON CONFLICT DO NOTHING;
            """
        )
    )

    conn = op.get_bind()
    parent_res = conn.execute(
        sa.text("SELECT id FROM categories WHERE slug = 'main_dishes' LIMIT 1")
    ).fetchone()
    if parent_res is not None:
        parent_id: int = int(parent_res[0])
        subcategories: list[tuple[str, str, int]] = [
            (
                "main_dishes_meat",
                '{"en": "Meat", "ru": "Мясо", "es": "Carne"}',
                1,
            ),
            (
                "main_dishes_fish",
                '{"en": "Fish", "ru": "Рыба", "es": "Pescado"}',
                2,
            ),
            (
                "main_dishes_veg",
                '{"en": "Vegetables", "ru": "Овощи", "es": "Verduras"}',
                3,
            ),
        ]
        for slug, name_json, order_idx in subcategories:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO categories (
                        parent_id,
                        name,
                        slug,
                        order_index,
                        created_at,
                        updated_at
                    )
                    SELECT
                        :parent_id,
                        CAST(:name AS jsonb),
                        :slug,
                        :order_index,
                        now(),
                        now()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM categories WHERE slug = :slug
                    )
                    """
                ),
                {
                    "parent_id": parent_id,
                    "name": name_json,
                    "slug": slug,
                    "order_index": order_idx,
                },
            )

    op.drop_index(
        "ix_recipes_category_id",
        table_name="recipes",
        if_exists=True,
    )
    op.drop_constraint(
        "recipes_category_id_fkey",
        "recipes",
        type_="foreignkey",
    )
    op.drop_column("recipes", "category_id")


def downgrade() -> None:
    op.add_column(
        "recipes",
        sa.Column("category_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "recipes_category_id_fkey",
        "recipes",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_recipes_category_id",
        "recipes",
        ["category_id"],
        unique=False,
    )

    op.execute(
        sa.text(
            """
            UPDATE recipes r
            SET category_id = (
                SELECT rc.category_id
                FROM recipe_categories rc
                WHERE rc.recipe_id = r.id
                ORDER BY rc.category_id ASC
                LIMIT 1
            )
            """
        )
    )

    op.drop_index(
        "ix_recipe_categories_category_id",
        table_name="recipe_categories",
        if_exists=True,
    )
    op.drop_table("recipe_categories")
