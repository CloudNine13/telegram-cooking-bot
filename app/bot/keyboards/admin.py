from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.callbacks import (
    AdminActionCallback,
    FridgeActionCallback,
    MainMenuCallback,
)
from app.core.i18n.helpers import get_localized_text
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.schemas.category import CategoryDTO


def get_admin_dashboard_keyboard(
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_admin_add_wizard", locale=locale),
            callback_data=AdminActionCallback(action="add_wizard").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_admin_add_template", locale=locale),
            callback_data=AdminActionCallback(action="add_template").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_admin_manage_categories", locale=locale),
            callback_data=AdminActionCallback(
                action="manage_categories",
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_fridge", locale=locale),
            callback_data=FridgeActionCallback(action="view").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_main_menu", locale=locale),
            callback_data=MainMenuCallback(target="main").pack(),
        ),
    )

    return builder.as_markup()


def get_admin_recipe_actions_keyboard(
    recipe_id: int,
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_admin_edit_recipe", locale=locale),
            callback_data=AdminActionCallback(
                action="edit_recipe",
                target_id=recipe_id,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_admin_delete_recipe", locale=locale),
            callback_data=AdminActionCallback(
                action="delete_recipe",
                target_id=recipe_id,
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=AdminActionCallback(action="dashboard").pack(),
        ),
    )

    return builder.as_markup()


def get_admin_edit_recipe_keyboard(
    recipe_id: int,
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_edit_title_en", locale=locale),
            callback_data=AdminActionCallback(
                action="edit_title_en",
                target_id=recipe_id,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_edit_title_ru", locale=locale),
            callback_data=AdminActionCallback(
                action="edit_title_ru",
                target_id=recipe_id,
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_edit_category", locale=locale),
            callback_data=AdminActionCallback(
                action="edit_category",
                target_id=recipe_id,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_edit_prep_time", locale=locale),
            callback_data=AdminActionCallback(
                action="edit_prep_time",
                target_id=recipe_id,
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_edit_ingredients", locale=locale),
            callback_data=AdminActionCallback(
                action="edit_ingredients",
                target_id=recipe_id,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_edit_instructions", locale=locale),
            callback_data=AdminActionCallback(
                action="edit_instructions",
                target_id=recipe_id,
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_edit_media", locale=locale),
            callback_data=AdminActionCallback(
                action="edit_media",
                target_id=recipe_id,
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=AdminActionCallback(action="dashboard").pack(),
        ),
    )

    return builder.as_markup()


def get_admin_delete_confirm_keyboard(
    recipe_id: int,
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_confirm_delete", locale=locale),
            callback_data=AdminActionCallback(
                action="delete_confirm",
                target_id=recipe_id,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_cancel", locale=locale),
            callback_data=AdminActionCallback(
                action="delete_cancel",
                target_id=recipe_id,
            ).pack(),
        ),
    )

    return builder.as_markup()


def get_admin_categories_keyboard(
    categories: list[CategoryDTO],
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    for category in categories:
        name: str = get_localized_text(category.name, locale=locale)
        builder.button(
            text=name,
            callback_data=AdminActionCallback(
                action="category_detail",
                target_id=category.id,
            ).pack(),
        )

    builder.adjust(2)

    add_cat_label: str
    if locale == "ru":
        add_cat_label = "➕ Добавить категорию"
    elif locale == "es":
        add_cat_label = "➕ Añadir Categoría"
    else:
        add_cat_label = "➕ Add Category"

    builder.row(
        InlineKeyboardButton(
            text=add_cat_label,
            callback_data=AdminActionCallback(action="add_category").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=AdminActionCallback(action="dashboard").pack(),
        ),
    )

    return builder.as_markup()


def get_admin_category_detail_keyboard(
    category_id: int,
    locale: str = DEFAULT_LOCALE,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    del_cat_label: str
    if locale == "ru":
        del_cat_label = "🗑️ Удалить категорию"
    elif locale == "es":
        del_cat_label = "🗑️ Eliminar Categoría"
    else:
        del_cat_label = "🗑️ Delete Category"

    builder.row(
        InlineKeyboardButton(
            text=del_cat_label,
            callback_data=AdminActionCallback(
                action="delete_category",
                target_id=category_id,
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_back", locale=locale),
            callback_data=AdminActionCallback(
                action="manage_categories",
            ).pack(),
        ),
    )

    return builder.as_markup()


def get_admin_category_select_keyboard(
    categories: list[CategoryDTO],
    locale: str = DEFAULT_LOCALE,
    include_none: bool = False,
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    if include_none:
        none_label: str
        if locale == "ru":
            none_label = "🔝 Верхний уровень (Нет)"
        elif locale == "es":
            none_label = "🔝 Nivel superior (Ninguna)"
        else:
            none_label = "🔝 Top-level (None)"

        builder.row(
            InlineKeyboardButton(
                text=none_label,
                callback_data=AdminActionCallback(
                    action="select_category",
                    target_id=0,
                ).pack(),
            ),
        )

    for category in categories:
        name: str = get_localized_text(category.name, locale=locale)
        builder.button(
            text=name,
            callback_data=AdminActionCallback(
                action="select_category",
                target_id=category.id,
            ).pack(),
        )

    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(
            text=t("btn_cancel", locale=locale),
            callback_data=AdminActionCallback(action="cancel").pack(),
        ),
    )

    return builder.as_markup()


def get_admin_cancel_keyboard(
    locale: str = DEFAULT_LOCALE,
    action: str = "cancel",
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_cancel", locale=locale),
            callback_data=AdminActionCallback(action=action).pack(),
        ),
    )

    return builder.as_markup()


def get_admin_skip_cancel_keyboard(
    locale: str = DEFAULT_LOCALE,
    skip_action: str = "skip",
    cancel_action: str = "cancel",
) -> InlineKeyboardMarkup:
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_skip", locale=locale),
            callback_data=AdminActionCallback(action=skip_action).pack(),
        ),
        InlineKeyboardButton(
            text=t("btn_cancel", locale=locale),
            callback_data=AdminActionCallback(action=cancel_action).pack(),
        ),
    )

    return builder.as_markup()
