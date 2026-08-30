from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.i18n.helpers import get_localized_text
from app.database.models.ingredient import Ingredient
from app.database.models.recipe import Recipe
from app.database.repositories.fridge_repo import FridgeRepo
from app.database.repositories.recipe_repo import RecipeRepo
from app.schemas.fridge import FridgeItemCreateDTO, RecipeMatchResultDTO
from app.schemas.recipe import RecipeDTO
from app.services.fridge_service import FridgeService


class FridgeMatcherService:
    def __init__(
        self,
        recipe_repo: RecipeRepo | None = None,
        fridge_repo: FridgeRepo | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        if recipe_repo is not None:
            self.recipe_repo: RecipeRepo = recipe_repo
        elif session is not None:
            self.recipe_repo = RecipeRepo(session)
        else:
            raise ValueError(
                "Either recipe_repo or session must be provided",
            )

        if fridge_repo is not None:
            self.fridge_repo: FridgeRepo = fridge_repo
        elif session is not None:
            self.fridge_repo = FridgeRepo(session)
        else:
            self.fridge_repo = FridgeRepo(self.recipe_repo.session)

    @staticmethod
    def is_ingredient_matched(
        ingredient: Ingredient,
        fridge_items: set[str],
    ) -> bool:
        norm: str = (ingredient.normalized_name or "").strip().lower()

        if norm in fridge_items:
            return True

        for item in fridge_items:
            if not item:
                continue

            if norm and (item in norm or norm in item):
                return True

        return False

    def match_recipe(
        self,
        recipe: Recipe,
        fridge_ingredients: set[str],
        locale: str = "en",
    ) -> RecipeMatchResultDTO:
        matched: list[str] = []
        missing: list[str] = []

        for ing in recipe.ingredients:
            display_name: str = ing.name

            if self.is_ingredient_matched(ing, fridge_ingredients):
                matched.append(display_name)
            else:
                missing.append(display_name)

        total_count: int = len(recipe.ingredients)
        matched_count: int = len(matched)
        missing_count: int = len(missing)

        if total_count == 0:
            percentage: float = 100.0
            is_full: bool = True
        else:
            percentage = round((matched_count / total_count) * 100.0, 1)
            is_full = missing_count == 0

        match_type: Literal["full", "partial"] = "full" if is_full else "partial"

        return RecipeMatchResultDTO(
            recipe=RecipeDTO.model_validate(recipe),
            match_type=match_type,
            matched_count=matched_count,
            missing_count=missing_count,
            match_percentage=percentage,
            matched_ingredients=matched,
            missing_ingredients=missing,
            is_full_match=is_full,
        )

    async def match_shared_fridge(
        self,
        match_type: Literal["full", "partial"],
        max_missing: int = 2,
        locale: str = "en",
    ) -> list[RecipeMatchResultDTO]:
        names: list[str] = await self.fridge_repo.get_normalized_names()
        if not names:
            return []

        fridge_set: set[str] = {item.strip().lower() for item in names if item}
        all_recipes: list[Recipe] = await self.recipe_repo.get_all_with_ingredients()

        results: list[RecipeMatchResultDTO] = []
        for recipe in all_recipes:
            res: RecipeMatchResultDTO = self.match_recipe(
                recipe=recipe,
                fridge_ingredients=fridge_set,
                locale=locale,
            )
            if (
                match_type == "full"
                and res.is_full_match
                or (
                    match_type == "partial"
                    and 1 <= len(res.missing_ingredients) <= max_missing
                )
            ):
                results.append(res)

        if match_type == "full":
            results.sort(
                key=lambda r: (
                    -r.match_percentage,
                    get_localized_text(r.recipe.title, locale=locale),
                ),
            )
        else:
            results.sort(
                key=lambda r: (
                    len(r.missing_ingredients),
                    -r.match_percentage,
                    get_localized_text(r.recipe.title, locale=locale),
                ),
            )

        return results

    async def match_instant_ingredients(
        self,
        raw_text: str,
        match_type: Literal["full", "partial"] = "partial",
        max_missing: int = 2,
        locale: str = "en",
    ) -> list[RecipeMatchResultDTO]:
        parsed: list[FridgeItemCreateDTO] = FridgeService.parse_raw_ingredients(
            raw_text,
        )
        if not parsed:
            return []

        fridge_set: set[str] = {
            item.normalized_name for item in parsed if item.normalized_name
        }
        all_recipes: list[Recipe] = await self.recipe_repo.get_all_with_ingredients()

        results: list[RecipeMatchResultDTO] = []
        for recipe in all_recipes:
            res: RecipeMatchResultDTO = self.match_recipe(
                recipe=recipe,
                fridge_ingredients=fridge_set,
                locale=locale,
            )
            if (
                match_type == "full"
                and res.is_full_match
                or (
                    match_type == "partial"
                    and res.matched_ingredients
                    and len(res.missing_ingredients) <= max_missing
                )
            ):
                results.append(res)

        results.sort(
            key=lambda r: (
                -r.match_percentage,
                len(r.missing_ingredients),
                get_localized_text(r.recipe.title, locale=locale),
            ),
        )

        return results

    async def search_by_ingredients(
        self,
        raw_ingredients_text: str,
        max_missing: int = 2,
        locale: str = "en",
    ) -> list[RecipeMatchResultDTO]:
        return await self.match_instant_ingredients(
            raw_text=raw_ingredients_text,
            match_type="partial",
            max_missing=max_missing,
            locale=locale,
        )
