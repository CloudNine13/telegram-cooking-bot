import json
import logging
import re
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.models.recipe import Recipe
from app.database.repositories.category_repo import CategoryRepo
from app.database.repositories.favorite_repo import FavoriteRepo
from app.database.repositories.recipe_repo import RecipeRepo
from app.schemas.common import PaginatedResponse, PaginationParams, SortOrder
from app.schemas.recipe import (
    RecipeCreateDTO,
    RecipeDTO,
    RecipeUpdateDTO,
)

logger: logging.Logger = logging.getLogger(__name__)

_shared_redis: Redis | None = None


def _get_default_redis() -> Redis | None:
    global _shared_redis
    if _shared_redis is None:
        try:
            settings = get_settings()
            _shared_redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        except (RedisError, ConnectionError, OSError) as exc:
            logger.debug("Could not initialize default Redis client: %s", exc)
            _shared_redis = None
    return _shared_redis


class RecipeService:
    def __init__(
        self,
        recipe_repo: RecipeRepo | None = None,
        category_repo: CategoryRepo | None = None,
        favorite_repo: FavoriteRepo | None = None,
        session: AsyncSession | None = None,
        redis: Redis | None = None,
    ) -> None:
        if recipe_repo is not None:
            self.recipe_repo: RecipeRepo = recipe_repo
        elif session is not None:
            self.recipe_repo = RecipeRepo(session)
        else:
            raise ValueError(
                "Either recipe_repo or session must be provided",
            )

        if category_repo is not None:
            self.category_repo: CategoryRepo = category_repo
        elif session is not None:
            self.category_repo = CategoryRepo(session)
        else:
            self.category_repo = CategoryRepo(self.recipe_repo.session)

        if favorite_repo is not None:
            self.favorite_repo: FavoriteRepo = favorite_repo
        elif session is not None:
            self.favorite_repo = FavoriteRepo(session)
        else:
            self.favorite_repo = FavoriteRepo(self.recipe_repo.session)

        self.session: AsyncSession = self.recipe_repo.session
        self.redis: Redis | None = redis if redis is not None else _get_default_redis()

    async def _get_search_cache(
        self,
        cache_key: str,
    ) -> tuple[list[RecipeDTO], int] | None:
        if self.redis is None:
            return None

        try:
            raw_val = await self.redis.get(cache_key)
            if raw_val is None:
                return None

            raw_str: str = (
                raw_val.decode("utf-8") if isinstance(raw_val, bytes) else str(raw_val)
            )
            parsed: dict[str, Any] = json.loads(raw_str)
            items: list[RecipeDTO] = [
                RecipeDTO.model_validate(item) for item in parsed.get("items", [])
            ]
            total_count: int = int(parsed.get("total_count", 0))

            return items, total_count
        except (RedisError, ConnectionError, OSError) as exc:
            logger.debug("Redis get cache error: %s", exc)
            return None

    async def _set_search_cache(
        self,
        cache_key: str,
        data: tuple[list[RecipeDTO], int],
        ttl: int = 600,
    ) -> None:
        if self.redis is None:
            return

        try:
            recipes, total_count = data
            payload: dict[str, Any] = {
                "items": [r.model_dump(mode="json") for r in recipes],
                "total_count": total_count,
            }
            await self.redis.set(cache_key, json.dumps(payload), ex=ttl)
        except (RedisError, ConnectionError, OSError) as exc:
            logger.debug("Redis set cache error: %s", exc)

    async def _invalidate_search_cache(self) -> None:
        if self.redis is None:
            return

        try:
            cursor: int = 0
            keys_to_delete: list[str] = []
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match="recipe_search:*",
                    count=100,
                )
                if keys:
                    for k in keys:
                        k_str: str = (
                            k.decode("utf-8") if isinstance(k, bytes) else str(k)
                        )
                        keys_to_delete.append(k_str)
                if cursor == 0:
                    break

            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
        except (RedisError, ConnectionError, OSError) as exc:
            logger.debug("Redis invalidate cache error: %s", exc)

    async def get_recipe(self, recipe_id: int) -> RecipeDTO | None:
        recipe: Recipe | None = await self.recipe_repo.get_by_id(recipe_id)
        if recipe is None:
            return None

        return RecipeDTO.model_validate(recipe)

    async def get_recipes_by_ids(
        self,
        recipe_ids: list[int],
    ) -> list[RecipeDTO]:
        recipes: list[Recipe] = await self.recipe_repo.get_by_ids(recipe_ids)

        return [RecipeDTO.model_validate(r) for r in recipes]

    async def list_by_category(
        self,
        category_id: int | None = None,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
        include_subcategories: bool = True,
    ) -> PaginatedResponse[RecipeDTO]:
        pagination_params = pagination if pagination is not None else PaginationParams()
        recipes, total_count = await self.recipe_repo.list_by_category(
            category_id=category_id,
            sort_order=sort_order,
            pagination=pagination_params,
            include_subcategories=include_subcategories,
        )

        return PaginatedResponse[RecipeDTO](
            items=[RecipeDTO.model_validate(r) for r in recipes],
            total_count=total_count,
            page=pagination_params.page,
            page_size=pagination_params.page_size,
        )

    async def search_in_category(
        self,
        category_id: int | None,
        query_text: str,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
        include_subcategories: bool = True,
    ) -> PaginatedResponse[RecipeDTO]:
        pagination_params = pagination if pagination is not None else PaginationParams()
        cache_key: str = (
            f"recipe_search:category:{category_id}:"
            f"{query_text.strip().lower()}:{sort_order.value}:"
            f"{pagination_params.page}:{pagination_params.page_size}:"
            f"{include_subcategories}"
        )
        cached = await self._get_search_cache(cache_key)
        if cached is not None:
            cached_recipes, cached_total = cached
            return PaginatedResponse[RecipeDTO](
                items=cached_recipes,
                total_count=cached_total,
                page=pagination_params.page,
                page_size=pagination_params.page_size,
            )

        recipes, total_count = await self.recipe_repo.search_in_category(
            category_id=category_id,
            query_text=query_text,
            sort_order=sort_order,
            pagination=pagination_params,
            include_subcategories=include_subcategories,
        )
        dto_items: list[RecipeDTO] = [RecipeDTO.model_validate(r) for r in recipes]
        await self._set_search_cache(cache_key, (dto_items, total_count))

        return PaginatedResponse[RecipeDTO](
            items=dto_items,
            total_count=total_count,
            page=pagination_params.page,
            page_size=pagination_params.page_size,
        )

    async def search_global(
        self,
        query_text: str,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[RecipeDTO]:
        pagination_params = pagination if pagination is not None else PaginationParams()
        cache_key: str = (
            f"recipe_search:global:{query_text.strip().lower()}:"
            f"{sort_order.value}:{pagination_params.page}:"
            f"{pagination_params.page_size}"
        )
        cached = await self._get_search_cache(cache_key)
        if cached is not None:
            cached_recipes, cached_total = cached
            return PaginatedResponse[RecipeDTO](
                items=cached_recipes,
                total_count=cached_total,
                page=pagination_params.page,
                page_size=pagination_params.page_size,
            )

        recipes, total_count = await self.recipe_repo.search_global(
            query_text=query_text,
            sort_order=sort_order,
            pagination=pagination_params,
        )
        dto_items: list[RecipeDTO] = [RecipeDTO.model_validate(r) for r in recipes]
        await self._set_search_cache(cache_key, (dto_items, total_count))

        return PaginatedResponse[RecipeDTO](
            items=dto_items,
            total_count=total_count,
            page=pagination_params.page,
            page_size=pagination_params.page_size,
        )

    async def create_recipe(self, dto: RecipeCreateDTO) -> RecipeDTO:
        recipe: Recipe = await self.recipe_repo.create(dto)
        await self.session.commit()
        await self._invalidate_search_cache()

        return RecipeDTO.model_validate(recipe)

    async def update_recipe(
        self,
        recipe_id: int,
        dto: RecipeUpdateDTO,
    ) -> RecipeDTO | None:
        recipe: Recipe | None = await self.recipe_repo.update(recipe_id, dto)
        if recipe is None:
            return None

        await self.session.commit()
        await self._invalidate_search_cache()

        return RecipeDTO.model_validate(recipe)

    async def delete_recipe(self, recipe_id: int) -> bool:
        result: bool = await self.recipe_repo.delete(recipe_id)
        if result:
            await self.session.commit()
            await self._invalidate_search_cache()

        return result

    async def toggle_favorite(self, user_id: int, recipe_id: int) -> bool:
        result: bool = await self.favorite_repo.toggle(user_id, recipe_id)
        await self.session.commit()

        return result

    async def is_favorite(self, user_id: int, recipe_id: int) -> bool:
        return await self.favorite_repo.is_favorite(user_id, recipe_id)

    async def get_user_favorites(
        self,
        user_id: int,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[RecipeDTO]:
        pagination_params = pagination if pagination is not None else PaginationParams()
        recipes, total_count = await self.favorite_repo.get_user_favorites(
            user_id=user_id,
            pagination=pagination_params,
        )

        return PaginatedResponse[RecipeDTO](
            items=[RecipeDTO.model_validate(r) for r in recipes],
            total_count=total_count,
            page=pagination_params.page,
            page_size=pagination_params.page_size,
        )

    async def get_user_favorite_recipe_ids(self, user_id: int) -> set[int]:
        return await self.favorite_repo.get_user_favorite_recipe_ids(user_id)

    @staticmethod
    def parse_ingredient_line(
        line: str,
    ) -> tuple[str, float | None, str | None]:
        cleaned_line: str = line.strip().lstrip("-*• ").strip()
        if not cleaned_line:
            return "", None, None

        delimiter: str | None = None
        for candidate in (" - ", " – ", " — ", "-", "–", "—"):
            if candidate in cleaned_line:
                delimiter = candidate
                break

        if delimiter is not None:
            parts: list[str] = cleaned_line.split(delimiter, 1)
            name: str = parts[0].strip()
            amount_str: str = parts[1].strip()

            qty_match = re.match(r"^([\d\.,]+)\s*(.*)$", amount_str)
            if qty_match:
                try:
                    qty: float = float(qty_match.group(1).replace(",", "."))
                    unit_raw: str = qty_match.group(2).strip()
                    unit: str | None = unit_raw[:50] if unit_raw else None

                    return name, qty, unit
                except ValueError:
                    return name, None, amount_str[:50] if amount_str else None

            return name, None, amount_str[:50] if amount_str else None

        return cleaned_line, None, None
