import re

from sqlalchemy.ext.asyncio import AsyncSession

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


class RecipeService:
    def __init__(
        self,
        recipe_repo: RecipeRepo | None = None,
        category_repo: CategoryRepo | None = None,
        favorite_repo: FavoriteRepo | None = None,
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
        category_id: int,
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
        category_id: int,
        query_text: str,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
        include_subcategories: bool = True,
    ) -> PaginatedResponse[RecipeDTO]:
        pagination_params = pagination if pagination is not None else PaginationParams()
        recipes, total_count = await self.recipe_repo.search_in_category(
            category_id=category_id,
            query_text=query_text,
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

    async def search_global(
        self,
        query_text: str,
        sort_order: SortOrder = SortOrder.DATE_ADDED,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[RecipeDTO]:
        pagination_params = pagination if pagination is not None else PaginationParams()
        recipes, total_count = await self.recipe_repo.search_global(
            query_text=query_text,
            sort_order=sort_order,
            pagination=pagination_params,
        )

        return PaginatedResponse[RecipeDTO](
            items=[RecipeDTO.model_validate(r) for r in recipes],
            total_count=total_count,
            page=pagination_params.page,
            page_size=pagination_params.page_size,
        )

    async def create_recipe(self, dto: RecipeCreateDTO) -> RecipeDTO:
        recipe: Recipe = await self.recipe_repo.create(dto)

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

        title_en: str = parsed.title_en or parsed.title_ru or ""
        title_ru: str = parsed.title_ru or parsed.title_en or ""
        instructions_en: str = parsed.instructions_en or parsed.instructions_ru or ""
        instructions_ru: str = parsed.instructions_ru or parsed.instructions_en or ""

        dto = RecipeCreateDTO(
            category_id=category_id,
            title_en=title_en,
            title_ru=title_ru,
            prep_time_minutes=parsed.prep_time_minutes,
            instructions_en=instructions_en,
            instructions_ru=instructions_ru,
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

        return RecipeDTO.model_validate(recipe)

    async def delete_recipe(self, recipe_id: int) -> bool:
        return await self.recipe_repo.delete(recipe_id)

    async def toggle_favorite(self, user_id: int, recipe_id: int) -> bool:
        return await self.favorite_repo.toggle(user_id, recipe_id)

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

        title_en: str | None = None
        title_ru: str | None = None
        category_slug: str | None = None
        prep_time_minutes: int = 0
        instructions_en_lines: list[str] = []
        instructions_ru_lines: list[str] = []
        ingredients_en_raw: list[str] = []
        ingredients_ru_raw: list[str] = []
        source_url: str | None = None
        instagram_url: str | None = None

        current_section: str | None = None

        for line in lines:
            lower_line: str = line.lower()

            if lower_line.startswith(("title (en):", "title en:")):
                current_section = None
                title_en = line.split(":", 1)[1].strip()
            elif lower_line.startswith(("title (ru):", "title ru:")):
                current_section = None
                title_ru = line.split(":", 1)[1].strip()
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
            elif (
                lower_line.startswith(("ingredients (en):", "ingredients en:"))
                or lower_line == "ingredients (en)"
            ):
                current_section = "ingredients_en"
            elif (
                lower_line.startswith(("ingredients (ru):", "ingredients ru:"))
                or lower_line == "ingredients (ru)"
            ):
                current_section = "ingredients_ru"
            elif (
                lower_line.startswith(
                    ("instructions (en):", "instructions en:"),
                )
                or lower_line == "instructions (en)"
            ):
                current_section = "instructions_en"
            elif (
                lower_line.startswith(
                    ("instructions (ru):", "instructions ru:"),
                )
                or lower_line == "instructions (ru)"
            ):
                current_section = "instructions_ru"
            else:
                if current_section == "ingredients_en":
                    ingredients_en_raw.append(line)
                elif current_section == "ingredients_ru":
                    ingredients_ru_raw.append(line)
                elif current_section == "instructions_en":
                    instructions_en_lines.append(line)
                elif current_section == "instructions_ru":
                    instructions_ru_lines.append(line)

        ingredients_dtos: list[IngredientCreateDTO] = []
        max_ing_len: int = max(
            len(ingredients_en_raw),
            len(ingredients_ru_raw),
        )

        for i in range(max_ing_len):
            en_line: str = ingredients_en_raw[i] if i < len(ingredients_en_raw) else ""
            ru_line: str = ingredients_ru_raw[i] if i < len(ingredients_ru_raw) else ""

            name_en, qty_en, unit_en = cls.parse_ingredient_line(en_line)
            name_ru, qty_ru, unit_ru = cls.parse_ingredient_line(ru_line)

            final_name_en: str = name_en or name_ru
            final_name_ru: str = name_ru or name_en
            final_qty: float | None = qty_en if qty_en is not None else qty_ru
            final_unit: str | None = unit_en if unit_en is not None else unit_ru

            if final_name_en or final_name_ru:
                ingredients_dtos.append(
                    IngredientCreateDTO(
                        name_en=final_name_en,
                        name_ru=final_name_ru,
                        quantity=final_qty,
                        unit=final_unit,
                    ),
                )

        instructions_en: str | None = (
            "\n".join(instructions_en_lines) if instructions_en_lines else None
        )
        instructions_ru: str | None = (
            "\n".join(instructions_ru_lines) if instructions_ru_lines else None
        )

        if not title_en and not title_ru:
            return None

        return ParsedRecipeTemplateDTO(
            title_en=title_en,
            title_ru=title_ru,
            category_slug=category_slug,
            prep_time_minutes=prep_time_minutes,
            instructions_en=instructions_en,
            instructions_ru=instructions_ru,
            source_url=source_url,
            instagram_url=instagram_url,
            ingredients=ingredients_dtos,
        )
