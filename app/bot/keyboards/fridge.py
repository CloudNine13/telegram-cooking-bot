from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.callbacks import (
    FridgeActionCallback,
    MainMenuCallback,
    RecipeViewCallback,
)
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.schemas.fridge import RecipeMatchResultDTO


def get_fridge_main_keyboard(
    items_count: int,
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_fridge_add", locale=locale),
            callback_data=FridgeActionCallback(action="add").pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_fridge_replace", locale=locale),
            callback_data=FridgeActionCallback(action="replace").pack(),
        ),
    )

    if items_count > 0:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_fridge_clear", locale=locale),
                callback_data=FridgeActionCallback(action="clear").pack(),
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text=t("btn_fridge_match_full", locale=locale),
                callback_data=FridgeActionCallback(action="match_full").pack(),
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text=t("btn_fridge_match_partial", locale=locale),
                callback_data=FridgeActionCallback(
                    action="match_partial",
                ).pack(),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_fridge_match_results_keyboard(
    matches: list[RecipeMatchResultDTO],
    match_type: str,
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    for match in matches:
        title: str = match.recipe.title_ru if locale == "ru" else match.recipe.title_en
        missing_count: int = len(match.missing_ingredients)
        btn_text: str = f"{title} (-{missing_count})" if missing_count > 0 else title

        builder.row(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=RecipeViewCallback(
                    recipe_id=match.recipe.id,
                    source=f"fridge_{match_type}",
                ).pack(),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=FridgeActionCallback(action="view").pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_fridge_cancel_keyboard(
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_cancel", locale=locale),
            callback_data=FridgeActionCallback(action="cancel").pack(),
        ),
    )

    return builder.as_markup()
