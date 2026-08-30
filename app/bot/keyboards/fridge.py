from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.callbacks import (
    FridgeActionCallback,
    MainMenuCallback,
    RecipeViewCallback,
)
from app.core.i18n.helpers import get_localized_text
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.schemas.fridge import FridgeItemDTO, RecipeMatchResultDTO


def get_fridge_main_keyboard(
    items_count: int,
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    if items_count > 0:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_fridge_match_full", locale=locale),
                callback_data=FridgeActionCallback(action="match_full").pack(),
            ),
            InlineKeyboardButton(
                text=t("btn_fridge_match_partial", locale=locale),
                callback_data=FridgeActionCallback(
                    action="match_partial",
                ).pack(),
            ),
        )
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
        builder.row(
            InlineKeyboardButton(
                text=t("btn_fridge_remove_items", locale=locale),
                callback_data=FridgeActionCallback(
                    action="delete_menu",
                ).pack(),
            ),
            InlineKeyboardButton(
                text=t("btn_fridge_clear", locale=locale),
                callback_data=FridgeActionCallback(action="clear").pack(),
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_fridge_add", locale=locale),
                callback_data=FridgeActionCallback(action="add").pack(),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_fridge_remove_items_keyboard(
    items: list[FridgeItemDTO],
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    for item in items:
        builder.button(
            text=f"❌ {item.raw_name}",
            callback_data=FridgeActionCallback(
                action="delete_item",
                item_id=item.id,
            ).pack(),
        )

    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=FridgeActionCallback(action="view").pack(),
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
        title: str = get_localized_text(match.recipe.title, locale=locale)
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

    back_cb: str = (
        MainMenuCallback(target="search").pack()
        if match_type == "instant"
        else FridgeActionCallback(action="view").pack()
    )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=back_cb,
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
