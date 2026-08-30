from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.category import Category
from app.database.repositories.category_repo import CategoryRepo
from app.schemas.category import (
    CategoryCreateDTO,
    CategoryDTO,
    CategoryUpdateDTO,
)

DEFAULT_CATEGORY_TAXONOMY: list[dict[str, Any]] = [
    {
        "slug": "breakfast",
        "name_en": "Breakfast",
        "name_ru": "Завтрак",
        "order_index": 1,
        "subcategories": [],
    },
    {
        "slug": "soups",
        "name_en": "First Courses / Soups",
        "name_ru": "Первые блюда",
        "order_index": 2,
        "subcategories": [],
    },
    {
        "slug": "main_dishes",
        "name_en": "Main Dishes",
        "name_ru": "Вторые блюда",
        "order_index": 3,
        "subcategories": [
            {
                "slug": "main_dishes_meat",
                "name_en": "Meat",
                "name_ru": "Мясо",
                "order_index": 1,
            },
            {
                "slug": "main_dishes_fish",
                "name_en": "Fish",
                "name_ru": "Рыба",
                "order_index": 2,
            },
            {
                "slug": "main_dishes_veg",
                "name_en": "Vegetables",
                "name_ru": "Овощи",
                "order_index": 3,
            },
        ],
    },
    {
        "slug": "salads",
        "name_en": "Salads",
        "name_ru": "Салаты",
        "order_index": 4,
        "subcategories": [],
    },
    {
        "slug": "appetizers",
        "name_en": "Appetizers",
        "name_ru": "Закуски",
        "order_index": 5,
        "subcategories": [],
    },
    {
        "slug": "desserts",
        "name_en": "Desserts",
        "name_ru": "Десерты",
        "order_index": 6,
        "subcategories": [],
    },
    {
        "slug": "beverages",
        "name_en": "Beverages",
        "name_ru": "Напитки",
        "order_index": 7,
        "subcategories": [],
    },
]


class CategoryService:
    def __init__(
        self,
        category_repo: CategoryRepo | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        if category_repo is not None:
            self.category_repo: CategoryRepo = category_repo
        elif session is not None:
            self.category_repo = CategoryRepo(session)
        else:
            raise ValueError(
                "Either category_repo or session must be provided",
            )
        self.session: AsyncSession = self.category_repo.session

    async def get_top_level_categories(self) -> list[CategoryDTO]:
        categories: list[Category] = await self.category_repo.get_top_level_categories()

        return [CategoryDTO.model_validate(c) for c in categories]

    async def get_subcategories(self, parent_id: int) -> list[CategoryDTO]:
        subcategories: list[Category] = await self.category_repo.get_subcategories(
            parent_id,
        )

        return [CategoryDTO.model_validate(c) for c in subcategories]

    async def get_category_by_id(self, category_id: int) -> CategoryDTO | None:
        category: Category | None = await self.category_repo.get_by_id(category_id)
        if category is None:
            return None

        return CategoryDTO.model_validate(category)

    async def get_category_by_slug(self, slug: str) -> CategoryDTO | None:
        category: Category | None = await self.category_repo.get_by_slug(slug)
        if category is None:
            return None

        return CategoryDTO.model_validate(category)

    async def get_category_tree(self) -> list[CategoryDTO]:
        categories: list[Category] = await self.category_repo.get_all_categories_tree()

        return [CategoryDTO.model_validate(c) for c in categories]

    async def get_all_categories(self) -> list[CategoryDTO]:
        categories: list[Category] = await self.category_repo.get_all()

        return [CategoryDTO.model_validate(c) for c in categories]

    async def create_category(self, dto: CategoryCreateDTO) -> CategoryDTO:
        category: Category = await self.category_repo.create(dto)
        await self.session.commit()

        return CategoryDTO.model_validate(category)

    async def update_category(
        self,
        category_id: int,
        dto: CategoryUpdateDTO,
    ) -> CategoryDTO | None:
        category: Category | None = await self.category_repo.update(
            category_id,
            dto,
        )
        if category is None:
            return None

        await self.session.commit()

        return CategoryDTO.model_validate(category)

    async def delete_category(self, category_id: int) -> bool:
        result: bool = await self.category_repo.delete(category_id)
        if result:
            await self.session.commit()

        return result

    async def seed_default_categories(self) -> list[CategoryDTO]:
        for cat_data in DEFAULT_CATEGORY_TAXONOMY:
            parent: Category | None = await self.category_repo.get_by_slug(
                cat_data["slug"],
            )
            if parent is None:
                parent_dto = CategoryCreateDTO(
                    slug=cat_data["slug"],
                    name_en=cat_data["name_en"],
                    name_ru=cat_data["name_ru"],
                    order_index=cat_data["order_index"],
                    parent_id=None,
                )
                parent = await self.category_repo.create(parent_dto)

            for sub_data in cat_data["subcategories"]:
                sub: Category | None = await self.category_repo.get_by_slug(
                    sub_data["slug"],
                )
                if sub is None:
                    sub_dto = CategoryCreateDTO(
                        slug=sub_data["slug"],
                        name_en=sub_data["name_en"],
                        name_ru=sub_data["name_ru"],
                        order_index=sub_data["order_index"],
                        parent_id=parent.id,
                    )
                    await self.category_repo.create(sub_dto)

        await self.session.commit()

        return await self.get_category_tree()
