from sqlalchemy import and_, case, delete, func, select, update
from sqlalchemy.orm import selectinload

from app.database.models.category import Category
from app.database.models.recipe import recipe_categories
from app.database.repositories.base import BaseRepo
from app.schemas.category import CategoryCreateDTO, CategoryUpdateDTO


class CategoryRepo(BaseRepo):
    async def get_orphan_recipe_ids_for_category(
        self,
        category_id: int,
    ) -> list[int]:
        subcat_stmt = select(Category.id).where(
            Category.parent_id == category_id,
        )
        subcat_res = await self.session.scalars(subcat_stmt)
        affected_ids: list[int] = [category_id, *list(subcat_res.all())]

        matching_count = func.count(
            case((recipe_categories.c.category_id.in_(affected_ids), 1)),
        )
        stmt = (
            select(recipe_categories.c.recipe_id)
            .group_by(recipe_categories.c.recipe_id)
            .having(
                and_(
                    func.count(recipe_categories.c.category_id) == matching_count,
                    matching_count > 0,
                ),
            )
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def get_by_id(self, category_id: int) -> Category | None:

        stmt = (
            select(Category)
            .where(Category.id == category_id)
            .options(
                selectinload(Category.subcategories).selectinload(
                    Category.subcategories,
                ),
            )
        )
        result = await self.session.scalars(stmt)

        return result.one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = (
            select(Category)
            .where(Category.slug == slug)
            .options(
                selectinload(Category.subcategories).selectinload(
                    Category.subcategories,
                ),
            )
        )
        result = await self.session.scalars(stmt)

        return result.one_or_none()

    async def get_top_level_categories(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.parent_id.is_(None))
            .options(
                selectinload(Category.subcategories).selectinload(
                    Category.subcategories,
                ),
            )
            .order_by(Category.order_index.asc(), Category.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def get_subcategories(self, parent_id: int) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.parent_id == parent_id)
            .options(selectinload(Category.subcategories))
            .order_by(Category.order_index.asc(), Category.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def get_all_categories_tree(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.parent_id.is_(None))
            .options(
                selectinload(Category.subcategories).selectinload(
                    Category.subcategories,
                ),
            )
            .order_by(Category.order_index.asc(), Category.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def get_all(self) -> list[Category]:
        stmt = (
            select(Category)
            .options(
                selectinload(Category.subcategories).selectinload(
                    Category.subcategories,
                ),
            )
            .order_by(Category.order_index.asc(), Category.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def create(self, dto: CategoryCreateDTO) -> Category:
        category = Category(
            parent_id=dto.parent_id,
            name=dto.name,
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
