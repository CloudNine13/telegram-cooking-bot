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
    IngredientCreateDTO,
    ParsedRecipeTemplateDTO,
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

    async def create_from_parsed_template(
        self,
        parsed: ParsedRecipeTemplateDTO,
        fallback_category_id: int | None = None,
    ) -> RecipeDTO:
        category_id: int | None = None

        if parsed.category_slug is not None:
            cat = await self.category_repo.get_by_slug(parsed.category_slug)
            if cat is not None:
                category_id = cat.id

        if category_id is None:
            category_id = fallback_category_id

        if category_id is None:
            raise ValueError("A valid category_id or category_slug is required")

        title: dict[str, str] = parsed.title.copy() if parsed.title else {}
        if parsed.title_en and "en" not in title:
            title["en"] = parsed.title_en
        if parsed.title_ru and "ru" not in title:
            title["ru"] = parsed.title_ru

        if not title:
            raise ValueError("Recipe title is required")

        instructions: str = (
            parsed.instructions
            or parsed.instructions_en
            or parsed.instructions_ru
            or ""
        )

        dto = RecipeCreateDTO(
            category_id=category_id,
            title=title,
            prep_time_minutes=parsed.prep_time_minutes,
            instructions=instructions,
            source_url=parsed.source_url,
            instagram_url=parsed.instagram_url,
            ingredients=parsed.ingredients,
        )

        return await self.create_recipe(dto)

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

        if "-" in cleaned_line:
            parts: list[str] = cleaned_line.split("-", 1)
            name: str = parts[0].strip()
            amount_str: str = parts[1].strip()
            qty_match = re.match(
                r"^([\d\.,]+)\s*([a-zA-Zа-яА-Я%°/]+)?",
                amount_str,
            )
            if qty_match:
                try:
                    qty: float = float(qty_match.group(1).replace(",", "."))
                    unit: str | None = (
                        qty_match.group(2).strip() if qty_match.group(2) else None
                    )

                    return name, qty, unit
                except ValueError:
                    return name, None, amount_str

            return name, None, amount_str

        return cleaned_line, None, None

    @classmethod
    def parse_recipe_template(
        cls,
        template_text: str,
    ) -> ParsedRecipeTemplateDTO | None:
        lines: list[str] = [
            line.strip() for line in template_text.splitlines() if line.strip()
        ]
        if not lines:
            return None

        title_dict: dict[str, str] = {}
        title_en: str | None = None
        title_ru: str | None = None
        category_slug: str | None = None
        prep_time_minutes: int = 0
        instructions_lines: list[str] = []
        ingredients_raw: list[str] = []
        source_url: str | None = None
        instagram_url: str | None = None

        current_section: str | None = None

        for line in lines:
            lower_line: str = line.lower()

            if lower_line.startswith(("title (en):", "title en:")):
                current_section = None
                title_en = line.split(":", 1)[1].strip()
                title_dict["en"] = title_en
            elif lower_line.startswith(("title (ru):", "title ru:")):
                current_section = None
                title_ru = line.split(":", 1)[1].strip()
                title_dict["ru"] = title_ru
            elif lower_line.startswith(("title (es):", "title es:")):
                current_section = None
                title_dict["es"] = line.split(":", 1)[1].strip()
            elif lower_line.startswith("title:"):
                current_section = None
                generic_title = line.split(":", 1)[1].strip()
                title_dict["en"] = generic_title
                title_dict["ru"] = generic_title
            elif lower_line.startswith("category:"):
                current_section = None
                category_slug = line.split(":", 1)[1].strip()
            elif lower_line.startswith(("prep time:", "time:")):
                current_section = None
                time_val_str = line.split(":", 1)[1].strip()
                match = re.search(r"\d+", time_val_str)
                if match:
                    prep_time_minutes = int(match.group())
            elif lower_line.startswith(("source url:", "source:")):
                current_section = None
                source_url = line.split(":", 1)[1].strip()
            elif lower_line.startswith(("instagram url:", "instagram:")):
                current_section = None
                instagram_url = line.split(":", 1)[1].strip()
            elif lower_line.startswith(
                (
                    "ingredients:",
                    "ingredients (en):",
                    "ingredients en:",
                    "ingredients (ru):",
                    "ingredients ru:",
                ),
            ) or lower_line in [
                "ingredients",
                "ingredients (en)",
                "ingredients (ru)",
            ]:
                current_section = "ingredients"
            elif lower_line.startswith(
                (
                    "instructions:",
                    "instructions (en):",
                    "instructions en:",
                    "instructions (ru):",
                    "instructions ru:",
                ),
            ) or lower_line in [
                "instructions",
                "instructions (en)",
                "instructions (ru)",
            ]:
                current_section = "instructions"
            else:
                if current_section == "ingredients":
                    ingredients_raw.append(line)
                elif current_section == "instructions":
                    instructions_lines.append(line)

        ingredients_dtos: list[IngredientCreateDTO] = []
        for ing_line in ingredients_raw:
            name, qty, unit = cls.parse_ingredient_line(ing_line)
            if name:
                ingredients_dtos.append(
                    IngredientCreateDTO(
                        name=name,
                        quantity=qty,
                        unit=unit,
                    ),
                )

        instructions_str: str | None = (
            "\n".join(instructions_lines) if instructions_lines else None
        )

        if not title_dict and not title_en and not title_ru:
            return None

        return ParsedRecipeTemplateDTO(
            title=title_dict,
            title_en=title_en,
            title_ru=title_ru,
            category_slug=category_slug,
            prep_time_minutes=prep_time_minutes,
            instructions=instructions_str,
            source_url=source_url,
            instagram_url=instagram_url,
            ingredients=ingredients_dtos,
        )
