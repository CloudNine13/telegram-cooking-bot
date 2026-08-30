from sqlalchemy import delete, func, select
from sqlalchemy.orm import joinedload, selectinload

from app.database.models.favorite import Favorite
from app.database.models.recipe import Recipe
from app.database.repositories.base import BaseRepo
from app.schemas.common import PaginationParams


class FavoriteRepo(BaseRepo):
    async def is_favorite(self, user_id: int, recipe_id: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(Favorite)
            .where(
                Favorite.user_id == user_id,
                Favorite.recipe_id == recipe_id,
            )
        )
        count_result: int | None = await self.session.scalar(stmt)

        return (count_result or 0) > 0

    async def toggle(self, user_id: int, recipe_id: int) -> bool:
        stmt = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.recipe_id == recipe_id,
        )
        result = await self.session.scalars(stmt)
        existing: Favorite | None = result.one_or_none()

        if existing is not None:
            await self.session.delete(existing)
            await self.session.flush()

            return False

        favorite = Favorite(user_id=user_id, recipe_id=recipe_id)
        self.session.add(favorite)
        await self.session.flush()

        return True

    async def add_favorite(self, user_id: int, recipe_id: int) -> Favorite:
        stmt = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.recipe_id == recipe_id,
        )
        result = await self.session.scalars(stmt)
        existing: Favorite | None = result.one_or_none()

        if existing is not None:
            return existing

        favorite = Favorite(user_id=user_id, recipe_id=recipe_id)
        self.session.add(favorite)
        await self.session.flush()

        return favorite

    async def remove_favorite(self, user_id: int, recipe_id: int) -> bool:
        stmt = delete(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.recipe_id == recipe_id,
        )
        result = await self.session.execute(stmt)

        return result.rowcount > 0

    async def get_user_favorites(
        self,
        user_id: int,
        pagination: PaginationParams | None = None,
    ) -> tuple[list[Recipe], int]:
        count_stmt = (
            select(func.count())
            .select_from(Favorite)
            .where(Favorite.user_id == user_id)
        )
        total_count: int | None = await self.session.scalar(count_stmt)

        stmt = (
            select(Recipe)
            .join(Favorite, Favorite.recipe_id == Recipe.id)
            .where(Favorite.user_id == user_id)
            .options(
                selectinload(Recipe.ingredients),
                joinedload(Recipe.category),
            )
            .order_by(Favorite.created_at.desc(), Recipe.id.desc())
        )

        if pagination is not None:
            stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

        result = await self.session.scalars(stmt)
        recipes: list[Recipe] = list(result.unique().all())

        return recipes, total_count or 0

    async def get_user_favorite_recipe_ids(self, user_id: int) -> set[int]:
        stmt = select(Favorite.recipe_id).where(Favorite.user_id == user_id)
        result = await self.session.scalars(stmt)

        return set(result.all())
