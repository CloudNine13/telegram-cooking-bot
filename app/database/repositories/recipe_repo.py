from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.orm import selectinload

from app.database.models.category import Category
from app.database.models.ingredient import Ingredient
from app.database.models.recipe import Recipe, recipe_categories
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
                selectinload(Recipe.categories).selectinload(Category.parent),
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
                selectinload(Recipe.categories).selectinload(Category.parent),
            )
        )
        result = await self.session.scalars(stmt)

        return list(result.unique().all())

    async def list_by_category(
        self,
        category_id: int | None = None,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
        include_subcategories: bool = True,
    ) -> tuple[list[Recipe], int]:
        category_ids: list[int] | None = None
        if category_id is not None and category_id != 0:
            category_ids = await self._resolve_category_ids(
                category_id,
                include_subcategories,
            )

        if category_ids is not None:
            count_stmt = (
                select(func.count(func.distinct(Recipe.id)))
                .select_from(Recipe)
                .join(
                    recipe_categories,
                    Recipe.id == recipe_categories.c.recipe_id,
                )
                .where(recipe_categories.c.category_id.in_(category_ids))
            )
        else:
            count_stmt = select(func.count()).select_from(Recipe)

        total_count: int | None = await self.session.scalar(count_stmt)

        stmt = select(Recipe).options(
            selectinload(Recipe.ingredients),
            selectinload(Recipe.categories).selectinload(Category.parent),
        )
        if category_ids is not None:
            stmt = (
                stmt.join(
                    recipe_categories,
                    Recipe.id == recipe_categories.c.recipe_id,
                )
                .where(recipe_categories.c.category_id.in_(category_ids))
                .distinct()
            )

        if sort_order == SortOrder.ALPHABETICAL:
            stmt = stmt.order_by(
                func.coalesce(Recipe.title.op("->>")("en"), "").asc(),
                Recipe.id.asc(),
            )
        else:
            stmt = stmt.order_by(Recipe.created_at.desc(), Recipe.id.desc())

        if pagination is not None:
            stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

        result = await self.session.scalars(stmt)
        recipes: list[Recipe] = list(result.unique().all())

        return recipes, total_count or 0

    async def search_in_category(
        self,
        category_id: int | None,
        query_text: str,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
        include_subcategories: bool = True,
    ) -> tuple[list[Recipe], int]:
        sim_en = func.similarity(
            func.coalesce(Recipe.title.op("->>")("en"), ""),
            query_text,
        )
        sim_ru = func.similarity(
            func.coalesce(Recipe.title.op("->>")("ru"), ""),
            query_text,
        )
        sim_es = func.similarity(
            func.coalesce(Recipe.title.op("->>")("es"), ""),
            query_text,
        )
        max_sim = func.greatest(sim_en, sim_ru, sim_es)

        ilike_condition = or_(
            Recipe.title.op("->>")("en").ilike(f"%{query_text}%"),
            Recipe.title.op("->>")("ru").ilike(f"%{query_text}%"),
            Recipe.title.op("->>")("es").ilike(f"%{query_text}%"),
        )
        title_search_filter = or_(max_sim >= 0.25, ilike_condition)

        category_ids: list[int] | None = None
        if category_id is not None and category_id != 0:
            category_ids = await self._resolve_category_ids(
                category_id,
                include_subcategories,
            )

        if category_ids is not None:
            count_stmt = (
                select(func.count(func.distinct(Recipe.id)))
                .select_from(Recipe)
                .join(
                    recipe_categories,
                    Recipe.id == recipe_categories.c.recipe_id,
                )
                .where(
                    and_(
                        recipe_categories.c.category_id.in_(category_ids),
                        title_search_filter,
                    ),
                )
            )
            stmt = (
                select(Recipe)
                .join(
                    recipe_categories,
                    Recipe.id == recipe_categories.c.recipe_id,
                )
                .where(
                    and_(
                        recipe_categories.c.category_id.in_(category_ids),
                        title_search_filter,
                    ),
                )
                .options(
                    selectinload(Recipe.ingredients),
                    selectinload(Recipe.categories).selectinload(Category.parent),
                )
                .distinct()
            )
        else:
            count_stmt = (
                select(func.count()).select_from(Recipe).where(title_search_filter)
            )
            stmt = (
                select(Recipe)
                .where(title_search_filter)
                .options(
                    selectinload(Recipe.ingredients),
                    selectinload(Recipe.categories).selectinload(Category.parent),
                )
            )

        total_count: int | None = await self.session.scalar(count_stmt)

        if sort_order == SortOrder.ALPHABETICAL:
            stmt = stmt.order_by(
                func.coalesce(Recipe.title.op("->>")("en"), "").asc(),
                Recipe.id.asc(),
            )
        else:
            stmt = stmt.order_by(max_sim.desc(), Recipe.id.desc())

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
        sim_en = func.similarity(
            func.coalesce(Recipe.title.op("->>")("en"), ""),
            query_text,
        )
        sim_ru = func.similarity(
            func.coalesce(Recipe.title.op("->>")("ru"), ""),
            query_text,
        )
        sim_es = func.similarity(
            func.coalesce(Recipe.title.op("->>")("es"), ""),
            query_text,
        )
        max_sim = func.greatest(sim_en, sim_ru, sim_es)

        ilike_condition = or_(
            Recipe.title.op("->>")("en").ilike(f"%{query_text}%"),
            Recipe.title.op("->>")("ru").ilike(f"%{query_text}%"),
            Recipe.title.op("->>")("es").ilike(f"%{query_text}%"),
        )
        title_search_filter = or_(max_sim >= 0.25, ilike_condition)

        ingredient_filter = Recipe.ingredients.any(
            or_(
                Ingredient.name.ilike(f"%{query_text}%"),
                Ingredient.normalized_name.ilike(f"%{query_text}%"),
            ),
        )

        where_clause = or_(title_search_filter, ingredient_filter)

        count_stmt = select(func.count()).select_from(Recipe).where(where_clause)
        total_count: int | None = await self.session.scalar(count_stmt)

        stmt = (
            select(Recipe)
            .where(where_clause)
            .options(
                selectinload(Recipe.ingredients),
                selectinload(Recipe.categories).selectinload(Category.parent),
            )
        )

        if sort_order == SortOrder.ALPHABETICAL:
            stmt = stmt.order_by(
                func.coalesce(Recipe.title.op("->>")("en"), "").asc(),
                Recipe.id.asc(),
            )
        else:
            stmt = stmt.order_by(max_sim.desc(), Recipe.id.desc())

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
                selectinload(Recipe.categories).selectinload(Category.parent),
            )
            .order_by(Recipe.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.unique().all())

    async def create(self, dto: RecipeCreateDTO) -> Recipe:
        recipe = Recipe(
            title=dto.title,
            prep_time_minutes=dto.prep_time_minutes,
            instructions=dto.instructions,
            photo_file_id=dto.photo_file_id,
            video_file_id=dto.video_file_id,
            document_file_id=dto.document_file_id,
            source_url=dto.source_url,
            instagram_url=dto.instagram_url,
        )
        self.session.add(recipe)
        await self.session.flush()

        for cat_id in dto.category_ids:
            cat_stmt = recipe_categories.insert().values(
                recipe_id=recipe.id,
                category_id=cat_id,
            )
            await self.session.execute(cat_stmt)

        for ing_dto in dto.ingredients:
            normalized: str = (
                ing_dto.normalized_name
                if ing_dto.normalized_name is not None
                else ing_dto.name.strip().lower()
            )
            ingredient = Ingredient(
                recipe_id=recipe.id,
                name=ing_dto.name,
                normalized_name=normalized,
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
                exclude={"ingredients", "category_ids"},
                exclude_unset=True,
            ).items()
            if v is not None
        }

        if update_data:
            stmt = update(Recipe).where(Recipe.id == recipe_id).values(**update_data)
            await self.session.execute(stmt)

        if dto.category_ids is not None:
            del_cat_stmt = delete(recipe_categories).where(
                recipe_categories.c.recipe_id == recipe_id,
            )
            await self.session.execute(del_cat_stmt)

            for cat_id in dto.category_ids:
                ins_cat_stmt = recipe_categories.insert().values(
                    recipe_id=recipe_id,
                    category_id=cat_id,
                )
                await self.session.execute(ins_cat_stmt)

        if dto.ingredients is not None:
            del_stmt = delete(Ingredient).where(
                Ingredient.recipe_id == recipe_id,
            )
            await self.session.execute(del_stmt)

            for ing_dto in dto.ingredients:
                normalized: str = (
                    ing_dto.normalized_name
                    if ing_dto.normalized_name is not None
                    else ing_dto.name.strip().lower()
                )
                ingredient = Ingredient(
                    recipe_id=recipe_id,
                    name=ing_dto.name,
                    normalized_name=normalized,
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
