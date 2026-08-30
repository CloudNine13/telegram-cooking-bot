from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.callbacks import (
    MainMenuCallback,
    PaginationCallback,
    RecipeViewCallback,
)
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.schemas.recipe import RecipeDTO


def get_favorites_keyboard(
    recipes: list[RecipeDTO],
    current_page: int,
    total_pages: int,
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    for recipe in recipes:
        title: str = recipe.title_ru if locale == "ru" else recipe.title_en
        builder.row(
            InlineKeyboardButton(
                text=title,
                callback_data=RecipeViewCallback(
                    recipe_id=recipe.id,
                    source="favorites",
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
                        target="favorites",
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
                    target="favorites",
                    page=current_page,
                ).pack(),
            ),
        )

        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=t("btn_next", locale=locale),
                    callback_data=PaginationCallback(
                        target="favorites",
                        page=current_page + 1,
                    ).pack(),
                ),
            )

        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()
