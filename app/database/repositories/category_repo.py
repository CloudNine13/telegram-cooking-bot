from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import selectinload

from app.database.models.category import Category
from app.database.repositories.base import BaseRepo
from app.schemas.category import CategoryCreateDTO, CategoryUpdateDTO


class CategoryRepo(BaseRepo):
    async def get_by_id(self, category_id: int) -> Category | None:
        stmt = (
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.subcategories))
        )
        result = await self.session.scalars(stmt)

        return result.one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = (
            select(Category)
            .where(Category.slug == slug)
            .options(selectinload(Category.subcategories))
        )
        result = await self.session.scalars(stmt)

        return result.one_or_none()

    async def get_top_level_categories(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.parent_id.is_(None))
            .options(selectinload(Category.subcategories))
            .order_by(Category.order_index.asc(), Category.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def get_subcategories(self, parent_id: int) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.parent_id == parent_id)
            .order_by(Category.order_index.asc(), Category.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def get_all_categories_tree(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.parent_id.is_(None))
            .options(selectinload(Category.subcategories))
            .order_by(Category.order_index.asc(), Category.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def get_all(self) -> list[Category]:
        stmt = (
            select(Category)
            .options(selectinload(Category.subcategories))
            .order_by(Category.order_index.asc(), Category.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def create(self, dto: CategoryCreateDTO) -> Category:
        category = Category(
            parent_id=dto.parent_id,
            name_en=dto.name_en,
            name_ru=dto.name_ru,
            slug=dto.slug,
            order_index=dto.order_index,
        )
        self.session.add(category)
        await self.session.flush()

        loaded_category: Category | None = await self.get_by_id(category.id)

        return loaded_category if loaded_category is not None else category

    async def update(
        self,
        category_id: int,
        dto: CategoryUpdateDTO,
    ) -> Category | None:
        update_data: dict[str, object] = {
            k: v for k, v in dto.model_dump(exclude_unset=True).items() if v is not None
        }
        if not update_data:
            return await self.get_by_id(category_id)

        stmt = update(Category).where(Category.id == category_id).values(**update_data)
        await self.session.execute(stmt)
        await self.session.flush()

        return await self.get_by_id(category_id)

    async def delete(self, category_id: int) -> bool:
        stmt = delete(Category).where(Category.id == category_id)
        result = await self.session.execute(stmt)

        return result.rowcount > 0

    async def count(self) -> int:
        stmt = select(func.count()).select_from(Category)
        count_result: int | None = await self.session.scalar(stmt)

        return count_result or 0
