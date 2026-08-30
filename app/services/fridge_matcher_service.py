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
    def _words_match(w1: str, w2: str) -> bool:
        if w1 == w2:
            return True

        s1: str = w1.rstrip("s")
        s2: str = w2.rstrip("s")
        if s1 == s2 and len(s1) >= 3:
            return True

        if w1.endswith("es") and w1[:-2] == w2 and len(w2) >= 3:
            return True

        if w2.endswith("es") and w2[:-2] == w1 and len(w1) >= 3:
            return True

        min_len: int = min(len(w1), len(w2))
        prefix_len: int = 0
        while prefix_len < min_len and w1[prefix_len] == w2[prefix_len]:
            prefix_len += 1

        if (
            prefix_len >= 4
            and abs(len(w1) - len(w2)) <= 3
            and prefix_len >= min_len - 2
        ):
            return True

        return (
            prefix_len >= 3
            and len(w1) <= 5
            and len(w2) <= 5
            and abs(len(w1) - len(w2)) <= 1
            and prefix_len >= min_len - 1
        )

    @classmethod
    def _match_tokens(
        cls,
        ing_words: list[str],
        item_words: list[str],
    ) -> bool:
        if len(item_words) == 1:
            item_word: str = item_words[0]
            return any(cls._words_match(item_word, w) for w in ing_words)

        if len(ing_words) == 1:
            ing_word: str = ing_words[0]
            return any(cls._words_match(ing_word, w) for w in item_words)

        item_in_ing: bool = all(
            any(cls._words_match(iw, iw_recipe) for iw_recipe in ing_words)
            for iw in item_words
        )
        if item_in_ing:
            return True

        ing_in_item: bool = all(
            any(cls._words_match(iw_recipe, iw) for iw in item_words)
            for iw_recipe in ing_words
        )

        return ing_in_item

    @classmethod
    def is_ingredient_matched(
        cls,
        ingredient: Ingredient,
        fridge_items: set[str],
    ) -> bool:
        raw_norm: str = ingredient.normalized_name or ingredient.name or ""
        norm: str = FridgeService.normalize_ingredient(raw_norm)
        if not norm:
            return False

        if norm in fridge_items:
            return True

        ing_words: list[str] = norm.split()
        if not ing_words:
            return False

        for item in fridge_items:
            if not item:
                continue

            if item == norm:
                return True

            item_words: list[str] = item.split()
            if not item_words:
                continue

            if cls._match_tokens(ing_words, item_words):
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
            is_full = missing_count == 0 and matched_count > 0

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

        fridge_set: set[str] = {
            FridgeService.normalize_ingredient(item) for item in names if item
        }
        fridge_set.discard("")
        if not fridge_set:
            return []

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
                    and res.matched_count > 0
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
                    and res.matched_count > 0
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
