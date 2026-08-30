from sqlalchemy.ext.asyncio import AsyncSession

from app.core.i18n.helpers import get_localized_text
from app.database.models.ingredient import Ingredient
from app.database.models.recipe import Recipe
from app.database.repositories.fridge_repo import FridgeRepo
from app.database.repositories.recipe_repo import RecipeRepo
from app.schemas.fridge import RecipeMatchResultDTO
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
        if total_count == 0:
            percentage: float = 100.0
            is_full: bool = True
        else:
            percentage = round((len(matched) / total_count) * 100.0, 1)
            is_full = len(missing) == 0

        return RecipeMatchResultDTO(
            recipe=RecipeDTO.model_validate(recipe),
            match_percentage=percentage,
            matched_ingredients=matched,
            missing_ingredients=missing,
            is_full_match=is_full,
        )

    async def find_full_matches(
        self,
        user_id: int,
        locale: str = "en",
    ) -> list[RecipeMatchResultDTO]:
        user_items: list[str] = await self.fridge_repo.get_user_normalized_names(
            user_id,
        )
        if not user_items:
            return []

        fridge_set: set[str] = {item.strip().lower() for item in user_items if item}
        all_recipes: list[Recipe] = await self.recipe_repo.get_all_with_ingredients()

        results: list[RecipeMatchResultDTO] = []
        for recipe in all_recipes:
            match_res: RecipeMatchResultDTO = self.match_recipe(
                recipe=recipe,
                fridge_ingredients=fridge_set,
                locale=locale,
            )
            if match_res.is_full_match:
                results.append(match_res)

        results.sort(
            key=lambda r: (
                -r.match_percentage,
                get_localized_text(r.recipe.title, locale=locale),
            ),
        )

        return results

    async def find_partial_matches(
        self,
        user_id: int,
        max_missing: int = 2,
        locale: str = "en",
    ) -> list[RecipeMatchResultDTO]:
        user_items: list[str] = await self.fridge_repo.get_user_normalized_names(
            user_id,
        )
        if not user_items:
            return []

        fridge_set: set[str] = {item.strip().lower() for item in user_items if item}
        all_recipes: list[Recipe] = await self.recipe_repo.get_all_with_ingredients()

        results: list[RecipeMatchResultDTO] = []
        for recipe in all_recipes:
            match_res: RecipeMatchResultDTO = self.match_recipe(
                recipe=recipe,
                fridge_ingredients=fridge_set,
                locale=locale,
            )
            missing_count: int = len(match_res.missing_ingredients)
            if 1 <= missing_count <= max_missing:
                results.append(match_res)

        results.sort(
            key=lambda r: (
                len(r.missing_ingredients),
                -r.match_percentage,
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
        parsed = FridgeService.parse_raw_ingredients(raw_ingredients_text)
        if not parsed:
            return []

        fridge_set: set[str] = {norm for _, norm in parsed if norm}
        all_recipes: list[Recipe] = await self.recipe_repo.get_all_with_ingredients()

        results: list[RecipeMatchResultDTO] = []
        for recipe in all_recipes:
            match_res: RecipeMatchResultDTO = self.match_recipe(
                recipe=recipe,
                fridge_ingredients=fridge_set,
                locale=locale,
            )
            if (
                match_res.matched_ingredients
                and len(match_res.missing_ingredients) <= max_missing
            ):
                results.append(match_res)

        results.sort(
            key=lambda r: (
                -r.match_percentage,
                len(r.missing_ingredients),
                get_localized_text(r.recipe.title, locale=locale),
            ),
        )

        return results
