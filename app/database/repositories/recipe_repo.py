from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.orm import joinedload, selectinload

from app.database.models.category import Category
from app.database.models.ingredient import Ingredient
from app.database.models.recipe import Recipe
from app.database.repositories.base import BaseRepo
from app.schemas.common import PaginationParams, SortOrder
from app.schemas.recipe import RecipeCreateDTO, RecipeUpdateDTO


class RecipeRepo(BaseRepo):
    async def _resolve_category_ids(
        self,
        category_id: int,
        include_subcategories: bool = True,
    ) -> list[int]:
        if not include_subcategories:
            return [category_id]

        stmt = select(Category.id).where(Category.parent_id == category_id)
        result = await self.session.scalars(stmt)
        subcategory_ids: list[int] = list(result.all())

        return [category_id, *subcategory_ids]

    async def get_by_id(self, recipe_id: int) -> Recipe | None:
        stmt = (
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(
                selectinload(Recipe.ingredients),
                joinedload(Recipe.category),
            )
        )
        result = await self.session.scalars(stmt)

        return result.unique().one_or_none()

    async def get_by_ids(self, recipe_ids: list[int]) -> list[Recipe]:
        if not recipe_ids:
            return []

        stmt = (
            select(Recipe)
            .where(Recipe.id.in_(recipe_ids))
            .options(
                selectinload(Recipe.ingredients),
                joinedload(Recipe.category),
            )
        )
        result = await self.session.scalars(stmt)

        return list(result.unique().all())

    async def list_by_category(
        self,
        category_id: int,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
        include_subcategories: bool = True,
    ) -> tuple[list[Recipe], int]:
        category_ids: list[int] = await self._resolve_category_ids(
            category_id,
            include_subcategories,
        )

        count_stmt = (
            select(func.count())
            .select_from(Recipe)
            .where(Recipe.category_id.in_(category_ids))
        )
        total_count: int | None = await self.session.scalar(count_stmt)

        stmt = (
            select(Recipe)
            .where(Recipe.category_id.in_(category_ids))
            .options(
                selectinload(Recipe.ingredients),
                joinedload(Recipe.category),
            )
        )

        if sort_order == SortOrder.ALPHABETICAL:
            stmt = stmt.order_by(Recipe.title_en.asc(), Recipe.id.asc())
        else:
            stmt = stmt.order_by(Recipe.created_at.desc(), Recipe.id.desc())

        if pagination is not None:
            stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

        result = await self.session.scalars(stmt)
        recipes: list[Recipe] = list(result.unique().all())

        return recipes, total_count or 0

    async def search_in_category(
        self,
        category_id: int,
        query_text: str,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
        include_subcategories: bool = True,
    ) -> tuple[list[Recipe], int]:
        category_ids: list[int] = await self._resolve_category_ids(
            category_id,
            include_subcategories,
        )
        search_filter = or_(
            Recipe.title_en.ilike(f"%{query_text}%"),
            Recipe.title_ru.ilike(f"%{query_text}%"),
        )
        where_clause = and_(
            Recipe.category_id.in_(category_ids),
            search_filter,
        )

        count_stmt = select(func.count()).select_from(Recipe).where(where_clause)
        total_count: int | None = await self.session.scalar(count_stmt)

        stmt = (
            select(Recipe)
            .where(where_clause)
            .options(
                selectinload(Recipe.ingredients),
                joinedload(Recipe.category),
            )
        )

        if sort_order == SortOrder.ALPHABETICAL:
            stmt = stmt.order_by(Recipe.title_en.asc(), Recipe.id.asc())
        else:
            stmt = stmt.order_by(Recipe.created_at.desc(), Recipe.id.desc())

        if pagination is not None:
            stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

        result = await self.session.scalars(stmt)
        recipes: list[Recipe] = list(result.unique().all())

        return recipes, total_count or 0

    async def search_global(
        self,
        query_text: str,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
    ) -> tuple[list[Recipe], int]:
        pattern: str = f"%{query_text}%"
        where_clause = or_(
            Recipe.title_en.ilike(pattern),
            Recipe.title_ru.ilike(pattern),
            Recipe.ingredients.any(
                or_(
                    Ingredient.name_en.ilike(pattern),
                    Ingredient.name_ru.ilike(pattern),
                    Ingredient.normalized_name_en.ilike(pattern),
                    Ingredient.normalized_name_ru.ilike(pattern),
                ),
            ),
        )

        count_stmt = select(func.count()).select_from(Recipe).where(where_clause)
        total_count: int | None = await self.session.scalar(count_stmt)

        stmt = (
            select(Recipe)
            .where(where_clause)
            .options(
                selectinload(Recipe.ingredients),
                joinedload(Recipe.category),
            )
        )

        if sort_order == SortOrder.ALPHABETICAL:
            stmt = stmt.order_by(Recipe.title_en.asc(), Recipe.id.asc())
        else:
            stmt = stmt.order_by(Recipe.created_at.desc(), Recipe.id.desc())

        if pagination is not None:
            stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

        result = await self.session.scalars(stmt)
        recipes: list[Recipe] = list(result.unique().all())

        return recipes, total_count or 0

    async def get_all_with_ingredients(self) -> list[Recipe]:
        stmt = (
            select(Recipe)
            .options(
                selectinload(Recipe.ingredients),
                joinedload(Recipe.category),
            )
            .order_by(Recipe.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.unique().all())

    async def create(self, dto: RecipeCreateDTO) -> Recipe:
        recipe = Recipe(
            category_id=dto.category_id,
            title_en=dto.title_en,
            title_ru=dto.title_ru,
            prep_time_minutes=dto.prep_time_minutes,
            instructions_en=dto.instructions_en,
            instructions_ru=dto.instructions_ru,
            photo_file_id=dto.photo_file_id,
            video_file_id=dto.video_file_id,
            document_file_id=dto.document_file_id,
            source_url=dto.source_url,
            instagram_url=dto.instagram_url,
        )
        self.session.add(recipe)
        await self.session.flush()

        for ing_dto in dto.ingredients:
            normalized_en: str = (
                ing_dto.normalized_name_en
                if ing_dto.normalized_name_en is not None
                else ing_dto.name_en.strip().lower()
            )
            normalized_ru: str = (
                ing_dto.normalized_name_ru
                if ing_dto.normalized_name_ru is not None
                else ing_dto.name_ru.strip().lower()
            )
            ingredient = Ingredient(
                recipe_id=recipe.id,
                name_en=ing_dto.name_en,
                name_ru=ing_dto.name_ru,
                normalized_name_en=normalized_en,
                normalized_name_ru=normalized_ru,
                quantity=ing_dto.quantity,
                unit=ing_dto.unit,
            )
            self.session.add(ingredient)

        await self.session.flush()

        loaded_recipe: Recipe | None = await self.get_by_id(recipe.id)

        return loaded_recipe if loaded_recipe is not None else recipe

    async def update(
        self,
        recipe_id: int,
        dto: RecipeUpdateDTO,
    ) -> Recipe | None:
        update_data: dict[str, object] = {
            k: v
            for k, v in dto.model_dump(
                exclude={"ingredients"},
                exclude_unset=True,
            ).items()
            if v is not None
        }

        if update_data:
            stmt = update(Recipe).where(Recipe.id == recipe_id).values(**update_data)
            await self.session.execute(stmt)

        if dto.ingredients is not None:
            del_stmt = delete(Ingredient).where(Ingredient.recipe_id == recipe_id)
            await self.session.execute(del_stmt)

            for ing_dto in dto.ingredients:
                normalized_en: str = (
                    ing_dto.normalized_name_en
                    if ing_dto.normalized_name_en is not None
                    else ing_dto.name_en.strip().lower()
                )
                normalized_ru: str = (
                    ing_dto.normalized_name_ru
                    if ing_dto.normalized_name_ru is not None
                    else ing_dto.name_ru.strip().lower()
                )
                ingredient = Ingredient(
                    recipe_id=recipe_id,
                    name_en=ing_dto.name_en,
                    name_ru=ing_dto.name_ru,
                    normalized_name_en=normalized_en,
                    normalized_name_ru=normalized_ru,
                    quantity=ing_dto.quantity,
                    unit=ing_dto.unit,
                )
                self.session.add(ingredient)

        await self.session.flush()

        return await self.get_by_id(recipe_id)

    async def delete(self, recipe_id: int) -> bool:
        stmt = delete(Recipe).where(Recipe.id == recipe_id)
        result = await self.session.execute(stmt)

        return result.rowcount > 0

    async def count(self) -> int:
        stmt = select(func.count()).select_from(Recipe)
        count_result: int | None = await self.session.scalar(stmt)

        return count_result or 0
