from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.callbacks import (
    AdminActionCallback,
    CatalogNavCallback,
    CategorySearchCallback,
    FavoriteToggleCallback,
    FridgeActionCallback,
    MainMenuCallback,
    PaginationCallback,
    RecipeMediaCallback,
    RecipeViewCallback,
    SortToggleCallback,
)
from app.core.i18n.helpers import get_localized_text
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.schemas.category import CategoryDTO
from app.schemas.common import SortOrder
from app.schemas.recipe import RecipeDTO


def get_top_categories_keyboard(
    categories: list[CategoryDTO],
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_all_recipes", locale=locale),
            callback_data=CatalogNavCallback(
                category_id=0,
                page=1,
                sort_order=SortOrder.DATE_ADDED,
            ).pack(),
        ),
    )

    for category in categories:
        name: str = get_localized_text(category.name, locale=locale)
        builder.button(
            text=name,
            callback_data=CatalogNavCallback(
                category_id=category.id,
                page=1,
                sort_order=SortOrder.DATE_ADDED,
            ).pack(),
        )

    builder.adjust(1, 2)

    builder.row(
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_subcategories_keyboard(
    parent: CategoryDTO,
    subcategories: list[CategoryDTO],
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    for subcategory in subcategories:
        name: str = get_localized_text(subcategory.name, locale=locale)
        builder.button(
            text=name,
            callback_data=CatalogNavCallback(
                category_id=subcategory.id,
                parent_id=parent.id,
                page=1,
                sort_order=SortOrder.DATE_ADDED,
            ).pack(),
        )

    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=CatalogNavCallback(category_id=None).pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_recipes_list_keyboard(
    recipes: list[RecipeDTO],
    category_id: int,
    current_page: int,
    total_pages: int,
    sort_order: SortOrder,
    locale: str = DEFAULT_LOCALE,
    parent_id: int | None = None,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    for recipe in recipes:
        title: str = get_localized_text(recipe.title, locale=locale)
        builder.row(
            InlineKeyboardButton(
                text=title,
                callback_data=RecipeViewCallback(
                    recipe_id=recipe.id,
                    source="catalog",
                    category_id=category_id,
                    page=current_page,
                ).pack(),
            ),
        )

    if total_pages > 1:
        nav_buttons: list[InlineKeyboardButton] = []

        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=t("btn_prev", locale=locale),
                    callback_data=CatalogNavCallback(
                        category_id=category_id,
                        parent_id=parent_id,
                        page=current_page - 1,
                        sort_order=sort_order,
                    ).pack(),
                ),
            )

        nav_buttons.append(
            InlineKeyboardButton(
                text=t(
                    "pagination_page",
                    locale=locale,
                    current=current_page,
                    total=total_pages,
                ),
                callback_data=CatalogNavCallback(
                    category_id=category_id,
                    parent_id=parent_id,
                    page=current_page,
                    sort_order=sort_order,
                ).pack(),
            ),
        )

        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=t("btn_next", locale=locale),
                    callback_data=CatalogNavCallback(
                        category_id=category_id,
                        parent_id=parent_id,
                        page=current_page + 1,
                        sort_order=sort_order,
                    ).pack(),
                ),
            )

        builder.row(*nav_buttons)

    sort_btn_text: str = (
        t("btn_sort_date", locale=locale)
        if sort_order == SortOrder.ALPHABETICAL
        else t("btn_sort_alpha", locale=locale)
    )
    next_sort: SortOrder = (
        SortOrder.DATE_ADDED
        if sort_order == SortOrder.ALPHABETICAL
        else SortOrder.ALPHABETICAL
    )

    builder.row(
        InlineKeyboardButton(
            text=sort_btn_text,
            callback_data=SortToggleCallback(
                category_id=category_id,
                current_sort=next_sort,
                parent_id=parent_id,
                page=1,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_search_category", locale=locale),
            callback_data=CategorySearchCallback(
                category_id=category_id,
            ).pack(),
        ),
    )

    back_callback = (
        CatalogNavCallback(category_id=parent_id).pack()
        if parent_id is not None
        else CatalogNavCallback(category_id=None).pack()
    )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=back_callback,
        ),
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_recipe_view_keyboard(
    recipe: RecipeDTO,
    is_favorite: bool,
    locale: str = DEFAULT_LOCALE,
    source: str = "catalog",
    category_id: int | None = None,
    page: int = 1,
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    fav_text: str = (
        t("btn_remove_favorite", locale=locale)
        if is_favorite
        else t("btn_add_favorite", locale=locale)
    )
    builder.row(
        InlineKeyboardButton(
            text=fav_text,
            callback_data=FavoriteToggleCallback(
                recipe_id=recipe.id,
                source=source,
                category_id=category_id,
                page=page,
            ).pack(),
        ),
    )

    media_buttons: list[InlineKeyboardButton] = []

    if recipe.document_file_id:
        media_buttons.append(
            InlineKeyboardButton(
                text=t("btn_view_pdf", locale=locale),
                callback_data=RecipeMediaCallback(
                    recipe_id=recipe.id,
                    media_type="pdf",
                ).pack(),
            ),
        )

    if recipe.video_file_id:
        media_buttons.append(
            InlineKeyboardButton(
                text=t("btn_view_video", locale=locale),
                callback_data=RecipeMediaCallback(
                    recipe_id=recipe.id,
                    media_type="video",
                ).pack(),
            ),
        )

    if media_buttons:
        builder.row(*media_buttons)

    link_buttons: list[InlineKeyboardButton] = []

    if recipe.source_url:
        link_buttons.append(
            InlineKeyboardButton(
                text=t("btn_source_link", locale=locale),
                url=recipe.source_url,
            ),
        )

    if recipe.instagram_url:
        link_buttons.append(
            InlineKeyboardButton(
                text=t("btn_instagram_link", locale=locale),
                url=recipe.instagram_url,
            ),
        )

    if link_buttons:
        builder.row(*link_buttons)

    if is_admin:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_edit_recipe", locale=locale),
                callback_data=AdminActionCallback(
                    action="edit_recipe",
                    target_id=recipe.id,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=t("btn_delete_recipe", locale=locale),
                callback_data=AdminActionCallback(
                    action="delete_recipe",
                    target_id=recipe.id,
                ).pack(),
            ),
        )

    back_callback_str: str

    if source == "catalog":
        back_callback_str = CatalogNavCallback(
            category_id=category_id,
            page=page,
        ).pack()
    elif source == "favorites":
        back_callback_str = PaginationCallback(
            target="favorites",
            page=page,
        ).pack()
    elif source == "fridge_full":
        back_callback_str = FridgeActionCallback(
            action="match_full",
        ).pack()
    elif source == "fridge_partial":
        back_callback_str = FridgeActionCallback(
            action="match_partial",
        ).pack()
    elif source == "fridge_instant" or source == "search":
        back_callback_str = MainMenuCallback(target="search").pack()
    else:
        back_callback_str = MainMenuCallback(target="main").pack()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=back_callback_str,
        ),
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_search_results_keyboard(
    recipes: list[RecipeDTO],
    current_page: int,
    total_pages: int,
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    for recipe in recipes:
        title: str = get_localized_text(recipe.title, locale=locale)
        builder.row(
            InlineKeyboardButton(
                text=title,
                callback_data=RecipeViewCallback(
                    recipe_id=recipe.id,
                    source="search",
                    page=current_page,
                ).pack(),
            ),
        )

    if total_pages > 1:
        nav_buttons: list[InlineKeyboardButton] = []

        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=t("btn_prev", locale=locale),
                    callback_data=PaginationCallback(
                        target="search",
                        page=current_page - 1,
                    ).pack(),
                ),
            )

        nav_buttons.append(
            InlineKeyboardButton(
                text=t(
                    "pagination_page",
                    locale=locale,
                    current=current_page,
                    total=total_pages,
                ),
                callback_data=PaginationCallback(
                    target="search",
                    page=current_page,
                ).pack(),
            ),
        )

        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=t("btn_next", locale=locale),
                    callback_data=PaginationCallback(
                        target="search",
                        page=current_page + 1,
                    ).pack(),
                ),
            )

        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=MainMenuCallback(target="search").pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()
