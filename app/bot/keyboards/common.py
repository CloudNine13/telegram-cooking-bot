from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.callbacks import (
    AdminActionCallback,
    CatalogNavCallback,
    FridgeActionCallback,
    LanguageSelectCallback,
    MainMenuCallback,
    PaginationCallback,
    SearchModeCallback,
)
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t


def get_main_menu_keyboard(
    locale: str = DEFAULT_LOCALE,
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_catalog", locale=locale),
            callback_data=CatalogNavCallback(category_id=None).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_search", locale=locale),
            callback_data=SearchModeCallback(mode="menu").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_fridge", locale=locale),
            callback_data=FridgeActionCallback(action="view").pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_favorites", locale=locale),
            callback_data=PaginationCallback(
                target="favorites",
                page=1,
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_language", locale=locale),
            callback_data=MainMenuCallback(target="language").pack(),
        ),
    )

    if is_admin:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_admin", locale=locale),
                callback_data=AdminActionCallback(action="dashboard").pack(),
            ),
        )

    return builder.as_markup()


def get_language_keyboard(
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🇬🇧 English",
            callback_data=LanguageSelectCallback(language_code="en").pack(),
        ),
        InlineKeyboardButton(
            text="🇷🇺 Русский",
            callback_data=LanguageSelectCallback(language_code="ru").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_search_menu_keyboard(
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_search_global", locale=locale),
            callback_data=SearchModeCallback(mode="global").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_search_instant", locale=locale),
            callback_data=SearchModeCallback(mode="instant").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_back_keyboard(
    target: str = "main",
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=MainMenuCallback(target=target).pack(),
        ),
    )

    return builder.as_markup()


def get_cancel_keyboard(
    locale: str = DEFAULT_LOCALE,
    target: str = "main",
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_cancel", locale=locale),
            callback_data=MainMenuCallback(target=target).pack(),
        ),
    )

    return builder.as_markup()
