from aiogram.filters.callback_data import CallbackData

from app.schemas.common import SortOrder


class CatalogNavCallback(CallbackData, prefix="cat_nav"):
    category_id: int | None = None
    parent_id: int | None = None
    page: int = 1
    sort_order: SortOrder = SortOrder.DATE_ADDED


class RecipeViewCallback(CallbackData, prefix="recipe_view"):
    recipe_id: int
    source: str = "catalog"
    category_id: int | None = None
    page: int = 1


class RecipeMediaCallback(CallbackData, prefix="recipe_media"):
    recipe_id: int
    media_type: str


class SortToggleCallback(CallbackData, prefix="sort_toggle"):
    category_id: int
    current_sort: SortOrder
    parent_id: int | None = None
    page: int = 1


class CategorySearchCallback(CallbackData, prefix="cat_search"):
    category_id: int


class FridgeActionCallback(CallbackData, prefix="fridge_act"):
    action: str
    item_id: int | None = None
    page: int = 1


class FavoriteToggleCallback(CallbackData, prefix="fav_toggle"):
    recipe_id: int
    source: str = "recipe"
    category_id: int | None = None
    page: int = 1


class AdminActionCallback(CallbackData, prefix="admin_act"):
    action: str
    target_id: int | None = None


class LanguageSelectCallback(CallbackData, prefix="lang_sel"):
    language_code: str


class PaginationCallback(CallbackData, prefix="page_nav"):
    target: str
    page: int
    category_id: int | None = None
    sort_order: SortOrder = SortOrder.DATE_ADDED


class MainMenuCallback(CallbackData, prefix="menu_nav"):
    target: str = "main"


class SearchModeCallback(CallbackData, prefix="search_mode"):
    mode: str
