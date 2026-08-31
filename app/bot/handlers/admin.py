import html
import re
from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.filters.admin import IsAdminFilter
from app.bot.keyboards.admin import (
    get_admin_cancel_keyboard,
    get_admin_categories_keyboard,
    get_admin_category_detail_keyboard,
    get_admin_category_select_keyboard,
    get_admin_dashboard_keyboard,
    get_admin_delete_confirm_keyboard,
    get_admin_edit_recipe_keyboard,
    get_admin_recipe_actions_keyboard,
    get_admin_skip_cancel_keyboard,
)
from app.bot.keyboards.callbacks import AdminActionCallback
from app.bot.states.recipe_wizard import (
    CategoryCreateWizard,
    RecipeCreateWizard,
    RecipeEditWizard,
    RecipeTemplateImportState,
)
from app.core.i18n.helpers import get_localized_text
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.schemas.category import CategoryCreateDTO, CategoryDTO
from app.schemas.recipe import (
    IngredientCreateDTO,
    ParsedRecipeTemplateDTO,
    RecipeCreateDTO,
    RecipeDTO,
    RecipeUpdateDTO,
)
from app.services.category_service import CategoryService
from app.services.media_downloader_service import MediaDownloaderService
from app.services.recipe_service import RecipeService

admin_router: Router = Router(name="admin")
admin_router.message.filter(IsAdminFilter())
admin_router.callback_query.filter(IsAdminFilter())


async def _edit_or_resend_message(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    if message.photo:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        await message.answer(
            text=text,
            reply_markup=reply_markup,
        )
        return

    try:
        await message.edit_text(
            text=text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        await message.answer(
            text=text,
            reply_markup=reply_markup,
        )


def _parse_wizard_ingredients(raw_text: str) -> list[IngredientCreateDTO]:
    lines: list[str] = [line.strip() for line in raw_text.splitlines() if line.strip()]
    dtos: list[IngredientCreateDTO] = []

    for line in lines:
        name, qty, unit = RecipeService.parse_ingredient_line(line)
        if name:
            dtos.append(
                IngredientCreateDTO(
                    name=name,
                    quantity=qty,
                    unit=unit,
                ),
            )

    return dtos


async def _save_wizard_recipe(
    recipe_service: RecipeService,
    state: FSMContext,
) -> RecipeDTO:
    data = await state.get_data()
    ingredients: list[IngredientCreateDTO] = _parse_wizard_ingredients(
        data.get("ingredients", ""),
    )

    title: dict[str, str] = {
        "en": str(data.get("title_en", "")),
        "ru": str(data.get("title_ru", "")),
    }

    dto = RecipeCreateDTO(
        category_id=int(data.get("category_id", 1)),
        title=title,
        prep_time_minutes=int(data.get("prep_time_minutes", 0)),
        instructions=str(data.get("instructions", "")),
        photo_file_id=data.get("photo_file_id"),
        video_file_id=data.get("video_file_id"),
        document_file_id=data.get("document_file_id"),
        source_url=data.get("source_url"),
        instagram_url=data.get("instagram_url"),
        ingredients=ingredients,
    )

    recipe: RecipeDTO = await recipe_service.create_recipe(dto)
    await state.clear()

    return recipe


@admin_router.message(Command("admin"))
async def handle_admin_command(
    message: Message,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    text: str = t("admin_menu", locale=locale)
    keyboard = get_admin_dashboard_keyboard(locale=locale)

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "dashboard"),
)
async def handle_admin_dashboard_callback(
    callback: CallbackQuery,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    text: str = t("admin_menu", locale=locale)
    keyboard = get_admin_dashboard_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(AdminActionCallback.filter(F.action == "cancel"))
async def handle_admin_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.clear()
    text: str = (
        f"{t('action_cancelled', locale=locale)}\n\n{t('admin_menu', locale=locale)}"
    )
    keyboard = get_admin_dashboard_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(Command("add_recipe"))
async def handle_add_recipe_command(
    message: Message,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.clear()
    await state.set_state(RecipeCreateWizard.title_en)
    text: str = t("admin_wizard_title_en", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "add_wizard"),
)
async def handle_add_wizard_callback(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.clear()
    await state.set_state(RecipeCreateWizard.title_en)
    text: str = t("admin_wizard_title_en", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(RecipeCreateWizard.title_en)
async def handle_wizard_title_en(
    message: Message,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    title_en: str = (message.text or "").strip()
    if not title_en:
        return

    await state.update_data(title_en=title_en)
    await state.set_state(RecipeCreateWizard.title_ru)
    text: str = t("admin_wizard_title_ru", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.message(RecipeCreateWizard.title_ru)
async def handle_wizard_title_ru(
    message: Message,
    category_service: CategoryService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    title_ru: str = (message.text or "").strip()
    if not title_ru:
        return

    await state.update_data(title_ru=title_ru)
    await state.set_state(RecipeCreateWizard.category_id)

    categories: list[CategoryDTO] = await category_service.get_all_categories()

    text: str = t("admin_wizard_category", locale=locale)
    keyboard = get_admin_category_select_keyboard(
        categories=categories,
        locale=locale,
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    RecipeCreateWizard.category_id,
    AdminActionCallback.filter(F.action == "select_category"),
)
async def handle_wizard_category_select(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    category_id: int = callback_data.target_id or 1
    await state.update_data(category_id=category_id)
    await state.set_state(RecipeCreateWizard.prep_time)

    text: str = t("admin_wizard_prep_time", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(RecipeCreateWizard.prep_time)
async def handle_wizard_prep_time(
    message: Message,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    raw_text: str = (message.text or "").strip()
    try:
        prep_time: int = int(raw_text)
        if prep_time < 0:
            raise ValueError
    except ValueError:
        await message.answer(
            text=t("error_invalid_number", locale=locale),
            reply_markup=get_admin_cancel_keyboard(locale=locale),
        )
        return

    await state.update_data(prep_time_minutes=prep_time)
    await state.set_state(RecipeCreateWizard.ingredients)
    text: str = t("admin_wizard_ingredients", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.message(RecipeCreateWizard.ingredients)
async def handle_wizard_ingredients(
    message: Message,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    ingredients_text: str = (message.text or "").strip()
    if not ingredients_text:
        return

    await state.update_data(ingredients=ingredients_text)
    await state.set_state(RecipeCreateWizard.instructions)
    text: str = t("admin_wizard_instructions", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.message(RecipeCreateWizard.instructions)
async def handle_wizard_instructions(
    message: Message,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    instructions_text: str = (message.text or "").strip()
    if not instructions_text:
        return

    await state.update_data(instructions=instructions_text)
    await state.set_state(RecipeCreateWizard.photo)
    text: str = t("admin_wizard_photo", locale=locale)
    keyboard = get_admin_skip_cancel_keyboard(
        locale=locale,
        skip_action="skip_photo",
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    RecipeCreateWizard.photo,
    AdminActionCallback.filter(F.action == "skip_photo"),
)
async def handle_wizard_skip_photo(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.set_state(RecipeCreateWizard.video)
    text: str = t("admin_wizard_video", locale=locale)
    keyboard = get_admin_skip_cancel_keyboard(
        locale=locale,
        skip_action="skip_video",
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(RecipeCreateWizard.photo)
async def handle_wizard_photo_message(
    message: Message,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if message.photo:
        photo_id: str = message.photo[-1].file_id
        await state.update_data(photo_file_id=photo_id)
    elif message.text and message.text.strip().lower() != "/skip":
        await state.update_data(photo_file_id=message.text.strip())

    await state.set_state(RecipeCreateWizard.video)
    text: str = t("admin_wizard_video", locale=locale)
    keyboard = get_admin_skip_cancel_keyboard(
        locale=locale,
        skip_action="skip_video",
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    RecipeCreateWizard.video,
    AdminActionCallback.filter(F.action == "skip_video"),
)
async def handle_wizard_skip_video(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.set_state(RecipeCreateWizard.pdf)
    text: str = t("admin_wizard_pdf", locale=locale)
    keyboard = get_admin_skip_cancel_keyboard(
        locale=locale,
        skip_action="skip_pdf",
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(RecipeCreateWizard.video)
async def handle_wizard_video_message(
    message: Message,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if message.video:
        await state.update_data(video_file_id=message.video.file_id)
    elif message.text and message.text.strip().lower() != "/skip":
        url: str = message.text.strip()
        if MediaDownloaderService.is_supported_url(url):
            await state.update_data(instagram_url=url)
        else:
            await state.update_data(video_file_id=url)

    await state.set_state(RecipeCreateWizard.pdf)
    text: str = t("admin_wizard_pdf", locale=locale)
    keyboard = get_admin_skip_cancel_keyboard(
        locale=locale,
        skip_action="skip_pdf",
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    RecipeCreateWizard.pdf,
    AdminActionCallback.filter(F.action == "skip_pdf"),
)
async def handle_wizard_skip_pdf(
    callback: CallbackQuery,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    recipe: RecipeDTO = await _save_wizard_recipe(
        recipe_service=recipe_service,
        state=state,
    )
    title: str = html.escape(get_localized_text(recipe.title, locale))
    text: str = t("admin_recipe_created", locale=locale, title=title)
    keyboard = get_admin_dashboard_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(RecipeCreateWizard.pdf)
async def handle_wizard_pdf_message(
    message: Message,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if message.document:
        await state.update_data(document_file_id=message.document.file_id)
    elif message.text and message.text.strip().lower() != "/skip":
        url: str = message.text.strip()
        if url.startswith(("http://", "https://")):
            await state.update_data(source_url=url)
        else:
            await state.update_data(document_file_id=url)

    recipe: RecipeDTO = await _save_wizard_recipe(
        recipe_service=recipe_service,
        state=state,
    )
    title: str = html.escape(get_localized_text(recipe.title, locale))
    text: str = t("admin_recipe_created", locale=locale, title=title)
    keyboard = get_admin_dashboard_keyboard(locale=locale)

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "add_template"),
)
async def handle_add_template_callback(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.clear()
    await state.set_state(RecipeTemplateImportState.waiting_for_template)
    text: str = t("admin_template_prompt", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(RecipeTemplateImportState.waiting_for_template)
async def handle_template_message(
    message: Message,
    category_service: CategoryService,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    raw_template: str = message.text or ""
    parsed: ParsedRecipeTemplateDTO | None = RecipeService.parse_recipe_template(
        raw_template,
    )

    if parsed is None:
        await message.answer(
            text=t("admin_template_invalid", locale=locale),
            reply_markup=get_admin_cancel_keyboard(locale=locale),
        )
        return

    top_categories: list[
        CategoryDTO
    ] = await category_service.get_top_level_categories()
    fallback_id: int = top_categories[0].id if top_categories else 1

    recipe: RecipeDTO = await recipe_service.create_from_parsed_template(
        parsed=parsed,
        fallback_category_id=fallback_id,
    )
    await state.clear()

    title: str = html.escape(get_localized_text(recipe.title, locale))
    text: str = t("admin_recipe_created", locale=locale, title=title)
    keyboard = get_admin_dashboard_keyboard(locale=locale)

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "edit_recipe"),
)
async def handle_edit_recipe_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    recipe_id: int | None = callback_data.target_id
    if recipe_id is None:
        await callback.answer()
        return

    recipe: RecipeDTO | None = await recipe_service.get_recipe(recipe_id)
    if recipe is None:
        await callback.answer(
            text=t("recipe_not_found", locale=locale),
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(RecipeEditWizard.select_field)
    await state.update_data(recipe_id=recipe_id)

    title: str = html.escape(get_localized_text(recipe.title, locale))
    text: str = t("admin_edit_select_field", locale=locale, title=title)
    keyboard = get_admin_edit_recipe_keyboard(
        recipe_id=recipe.id,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "edit_title_en"),
)
async def handle_edit_title_en_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if callback_data.target_id is not None:
        await state.update_data(recipe_id=callback_data.target_id)
    await state.set_state(RecipeEditWizard.title_en)
    text: str = t("admin_edit_prompt_title_en", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "edit_title_ru"),
)
async def handle_edit_title_ru_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if callback_data.target_id is not None:
        await state.update_data(recipe_id=callback_data.target_id)
    await state.set_state(RecipeEditWizard.title_ru)
    text: str = t("admin_edit_prompt_title_ru", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "edit_category"),
)
async def handle_edit_category_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    category_service: CategoryService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if callback_data.target_id is not None:
        await state.update_data(recipe_id=callback_data.target_id)
    await state.set_state(RecipeEditWizard.category_id)

    categories: list[CategoryDTO] = await category_service.get_all_categories()

    text: str = t("admin_edit_prompt_category", locale=locale)
    keyboard = get_admin_category_select_keyboard(
        categories=categories,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "edit_prep_time"),
)
async def handle_edit_prep_time_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if callback_data.target_id is not None:
        await state.update_data(recipe_id=callback_data.target_id)
    await state.set_state(RecipeEditWizard.prep_time)
    text: str = t("admin_edit_prompt_prep_time", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "edit_ingredients"),
)
async def handle_edit_ingredients_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if callback_data.target_id is not None:
        await state.update_data(recipe_id=callback_data.target_id)
    await state.set_state(RecipeEditWizard.ingredients)
    text: str = t("admin_edit_prompt_ingredients", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "edit_instructions"),
)
async def handle_edit_instructions_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if callback_data.target_id is not None:
        await state.update_data(recipe_id=callback_data.target_id)
    await state.set_state(RecipeEditWizard.instructions)
    text: str = t("admin_edit_prompt_instructions", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "edit_media"),
)
async def handle_edit_media_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if callback_data.target_id is not None:
        await state.update_data(recipe_id=callback_data.target_id)
    await state.set_state(RecipeEditWizard.media)
    text: str = t("admin_edit_prompt_media", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(RecipeEditWizard.title_en)
async def handle_edit_title_en_input(
    message: Message,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    title_en: str = (message.text or "").strip()
    if not title_en:
        return

    data = await state.get_data()
    recipe_id: int | None = data.get("recipe_id")
    if recipe_id is None:
        await state.clear()
        return

    existing: RecipeDTO | None = await recipe_service.get_recipe(recipe_id)
    title_dict: dict[str, str] = existing.title.copy() if existing else {}
    title_dict["en"] = title_en

    updated: RecipeDTO | None = await recipe_service.update_recipe(
        recipe_id=recipe_id,
        dto=RecipeUpdateDTO(title=title_dict),
    )
    await state.clear()

    title: str = (
        html.escape(get_localized_text(updated.title, locale)) if updated else title_en
    )
    text: str = t("admin_recipe_updated", locale=locale, title=title)
    keyboard = get_admin_recipe_actions_keyboard(
        recipe_id=recipe_id,
        locale=locale,
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.message(RecipeEditWizard.title_ru)
async def handle_edit_title_ru_input(
    message: Message,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    title_ru: str = (message.text or "").strip()
    if not title_ru:
        return

    data = await state.get_data()
    recipe_id: int | None = data.get("recipe_id")
    if recipe_id is None:
        await state.clear()
        return

    existing: RecipeDTO | None = await recipe_service.get_recipe(recipe_id)
    title_dict: dict[str, str] = existing.title.copy() if existing else {}
    title_dict["ru"] = title_ru

    updated: RecipeDTO | None = await recipe_service.update_recipe(
        recipe_id=recipe_id,
        dto=RecipeUpdateDTO(title=title_dict),
    )
    await state.clear()

    title: str = (
        html.escape(get_localized_text(updated.title, locale)) if updated else title_ru
    )
    text: str = t("admin_recipe_updated", locale=locale, title=title)
    keyboard = get_admin_recipe_actions_keyboard(
        recipe_id=recipe_id,
        locale=locale,
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    RecipeEditWizard.category_id,
    AdminActionCallback.filter(F.action == "select_category"),
)
async def handle_edit_category_select(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    category_id: int = callback_data.target_id or 1
    data = await state.get_data()
    recipe_id: int | None = data.get("recipe_id")
    if recipe_id is None:
        await state.clear()
        await callback.answer()
        return

    updated: RecipeDTO | None = await recipe_service.update_recipe(
        recipe_id=recipe_id,
        dto=RecipeUpdateDTO(category_id=category_id),
    )
    await state.clear()

    title: str = (
        html.escape(get_localized_text(updated.title, locale)) if updated else ""
    )
    text: str = t("admin_recipe_updated", locale=locale, title=title)
    keyboard = get_admin_recipe_actions_keyboard(
        recipe_id=recipe_id,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(RecipeEditWizard.prep_time)
async def handle_edit_prep_time_input(
    message: Message,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    raw_text: str = (message.text or "").strip()
    try:
        prep_time: int = int(raw_text)
        if prep_time < 0:
            raise ValueError
    except ValueError:
        await message.answer(
            text=t("error_invalid_number", locale=locale),
            reply_markup=get_admin_cancel_keyboard(locale=locale),
        )
        return

    data = await state.get_data()
    recipe_id: int | None = data.get("recipe_id")
    if recipe_id is None:
        await state.clear()
        return

    updated: RecipeDTO | None = await recipe_service.update_recipe(
        recipe_id=recipe_id,
        dto=RecipeUpdateDTO(prep_time_minutes=prep_time),
    )
    await state.clear()

    title: str = (
        html.escape(get_localized_text(updated.title, locale)) if updated else ""
    )
    text: str = t("admin_recipe_updated", locale=locale, title=title)
    keyboard = get_admin_recipe_actions_keyboard(
        recipe_id=recipe_id,
        locale=locale,
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.message(RecipeEditWizard.ingredients)
async def handle_edit_ingredients_input(
    message: Message,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    raw_text: str = (message.text or "").strip()
    if not raw_text:
        return

    data = await state.get_data()
    recipe_id: int | None = data.get("recipe_id")
    if recipe_id is None:
        await state.clear()
        return

    ingredients: list[IngredientCreateDTO] = _parse_wizard_ingredients(
        raw_text,
    )
    updated: RecipeDTO | None = await recipe_service.update_recipe(
        recipe_id=recipe_id,
        dto=RecipeUpdateDTO(ingredients=ingredients),
    )
    await state.clear()

    title: str = (
        html.escape(get_localized_text(updated.title, locale)) if updated else ""
    )
    text: str = t("admin_recipe_updated", locale=locale, title=title)
    keyboard = get_admin_recipe_actions_keyboard(
        recipe_id=recipe_id,
        locale=locale,
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.message(RecipeEditWizard.instructions)
async def handle_edit_instructions_input(
    message: Message,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    instructions_text: str = (message.text or "").strip()
    if not instructions_text:
        return

    data = await state.get_data()
    recipe_id: int | None = data.get("recipe_id")
    if recipe_id is None:
        await state.clear()
        return

    updated: RecipeDTO | None = await recipe_service.update_recipe(
        recipe_id=recipe_id,
        dto=RecipeUpdateDTO(instructions=instructions_text),
    )
    await state.clear()

    title: str = (
        html.escape(get_localized_text(updated.title, locale)) if updated else ""
    )
    text: str = t("admin_recipe_updated", locale=locale, title=title)
    keyboard = get_admin_recipe_actions_keyboard(
        recipe_id=recipe_id,
        locale=locale,
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.message(RecipeEditWizard.media)
async def handle_edit_media_input(
    message: Message,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    data = await state.get_data()
    recipe_id: int | None = data.get("recipe_id")
    if recipe_id is None:
        await state.clear()
        return

    dto: RecipeUpdateDTO = RecipeUpdateDTO()
    if message.photo:
        photo_id: str = message.photo[-1].file_id
        dto = RecipeUpdateDTO(photo_file_id=photo_id)
    elif message.video:
        video_id: str = message.video.file_id
        dto = RecipeUpdateDTO(video_file_id=video_id)
    elif message.document:
        doc_id: str = message.document.file_id
        dto = RecipeUpdateDTO(document_file_id=doc_id)
    elif message.text:
        raw_text: str = message.text.strip()
        if raw_text.lower() == "/clear":
            dto = RecipeUpdateDTO(
                photo_file_id="",
                video_file_id="",
                document_file_id="",
                source_url="",
                instagram_url="",
            )
        elif MediaDownloaderService.is_supported_url(raw_text):
            dto = RecipeUpdateDTO(instagram_url=raw_text)
        elif raw_text.startswith(("http://", "https://")):
            dto = RecipeUpdateDTO(source_url=raw_text)
        else:
            dto = RecipeUpdateDTO(photo_file_id=raw_text)

    updated: RecipeDTO | None = await recipe_service.update_recipe(
        recipe_id=recipe_id,
        dto=dto,
    )
    await state.clear()

    title: str = (
        html.escape(get_localized_text(updated.title, locale)) if updated else ""
    )
    text: str = t("admin_recipe_updated", locale=locale, title=title)
    keyboard = get_admin_recipe_actions_keyboard(
        recipe_id=recipe_id,
        locale=locale,
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "delete_recipe"),
)
async def handle_delete_recipe_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    recipe_service: RecipeService,
    locale: str = DEFAULT_LOCALE,
) -> None:
    recipe_id: int | None = callback_data.target_id
    if recipe_id is None:
        await callback.answer()
        return

    recipe: RecipeDTO | None = await recipe_service.get_recipe(recipe_id)
    if recipe is None:
        await callback.answer(
            text=t("recipe_not_found", locale=locale),
            show_alert=True,
        )
        return

    title: str = html.escape(get_localized_text(recipe.title, locale))
    text: str = t("admin_recipe_delete_confirm", locale=locale, title=title)
    keyboard = get_admin_delete_confirm_keyboard(
        recipe_id=recipe.id,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "delete_confirm"),
)
async def handle_delete_confirm_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    recipe_service: RecipeService,
    locale: str = DEFAULT_LOCALE,
) -> None:
    recipe_id: int | None = callback_data.target_id
    if recipe_id is not None:
        await recipe_service.delete_recipe(recipe_id)

    text: str = t("admin_recipe_deleted", locale=locale)
    keyboard = get_admin_dashboard_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "delete_cancel"),
)
async def handle_delete_cancel_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    recipe_service: RecipeService,
    locale: str = DEFAULT_LOCALE,
) -> None:
    recipe_id: int | None = callback_data.target_id
    if recipe_id is not None:
        recipe: RecipeDTO | None = await recipe_service.get_recipe(recipe_id)
        if recipe is not None:
            title: str = html.escape(get_localized_text(recipe.title, locale))
            keyboard = get_admin_recipe_actions_keyboard(
                recipe_id=recipe.id,
                locale=locale,
            )
            if callback.message is not None:
                await _edit_or_resend_message(
                    message=callback.message,
                    text=f"🍽️ <b>{title}</b>",
                    reply_markup=keyboard,
                )
            await callback.answer()
            return

    text: str = t("admin_menu", locale=locale)
    keyboard = get_admin_dashboard_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(Command("manage_categories"))
async def handle_manage_categories_command(
    message: Message,
    category_service: CategoryService,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    categories: list[CategoryDTO] = await category_service.get_all_categories()

    cat_mgmt_title: str
    if locale == "ru":
        cat_mgmt_title = "📁 Управление категориями"
    elif locale == "es":
        cat_mgmt_title = "📁 Gestión de Categorías"
    else:
        cat_mgmt_title = "📁 Category Management"

    keyboard = get_admin_categories_keyboard(
        categories=categories,
        locale=locale,
    )

    await message.answer(
        text=cat_mgmt_title,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "manage_categories"),
)
async def handle_manage_categories_callback(
    callback: CallbackQuery,
    category_service: CategoryService,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    categories: list[CategoryDTO] = await category_service.get_all_categories()

    cat_mgmt_title: str
    if locale == "ru":
        cat_mgmt_title = "📁 Управление категориями"
    elif locale == "es":
        cat_mgmt_title = "📁 Gestión de Categorías"
    else:
        cat_mgmt_title = "📁 Category Management"

    keyboard = get_admin_categories_keyboard(
        categories=categories,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=cat_mgmt_title,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "category_detail"),
)
async def handle_category_detail_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    category_service: CategoryService,
    locale: str = DEFAULT_LOCALE,
) -> None:
    category_id: int | None = callback_data.target_id
    if category_id is None:
        await callback.answer()
        return

    category: CategoryDTO | None = await category_service.get_category_by_id(
        category_id,
    )
    if category is None:
        await callback.answer(text="Category not found", show_alert=True)
        return

    name: str = html.escape(get_localized_text(category.name, locale))
    text: str = f"📁 <b>{name}</b> (<code>{category.slug}</code>)\nID: {category.id}"
    keyboard = get_admin_category_detail_keyboard(
        category_id=category.id,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "delete_category"),
)
async def handle_delete_category_callback(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    category_service: CategoryService,
    locale: str = DEFAULT_LOCALE,
) -> None:
    category_id: int | None = callback_data.target_id
    if category_id is not None:
        await category_service.delete_category(category_id)

    categories: list[CategoryDTO] = await category_service.get_all_categories()

    cat_mgmt_title: str
    if locale == "ru":
        cat_mgmt_title = "📁 Управление категориями"
    elif locale == "es":
        cat_mgmt_title = "📁 Gestión de Categorías"
    else:
        cat_mgmt_title = "📁 Category Management"

    text: str = f"{t('admin_category_deleted', locale=locale)}\n\n{cat_mgmt_title}"
    keyboard = get_admin_categories_keyboard(
        categories=categories,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.callback_query(
    AdminActionCallback.filter(F.action == "add_category"),
)
async def handle_add_category_callback(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.clear()
    await state.set_state(CategoryCreateWizard.name)
    text: str = t("admin_category_prompt_name", locale=locale)
    keyboard = get_admin_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@admin_router.message(CategoryCreateWizard.name)
async def handle_category_name(
    message: Message,
    category_service: CategoryService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    name: str = (message.text or "").strip()
    if not name:
        return

    await state.update_data(name=name)
    await state.set_state(CategoryCreateWizard.parent_id)

    top_categories: list[
        CategoryDTO
    ] = await category_service.get_top_level_categories()

    text: str = t("admin_category_prompt_parent", locale=locale)
    keyboard = get_admin_category_select_keyboard(
        categories=top_categories,
        locale=locale,
        include_none=True,
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@admin_router.callback_query(
    CategoryCreateWizard.parent_id,
    AdminActionCallback.filter(F.action == "select_category"),
)
async def handle_category_parent_select(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    category_service: CategoryService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    parent_id: int | None = (
        callback_data.target_id
        if callback_data.target_id and callback_data.target_id > 0
        else None
    )
    data = await state.get_data()
    name: str = data.get("name", "")

    slug: str = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")
    if not slug:
        slug = f"cat_{int(datetime.now(UTC).timestamp())}"

    dto = CategoryCreateDTO(
        slug=slug,
        name={"en": name},
        parent_id=parent_id,
    )
    new_cat: CategoryDTO = await category_service.create_category(dto)
    await state.clear()

    categories: list[CategoryDTO] = await category_service.get_all_categories()
    cat_name: str = html.escape(get_localized_text(new_cat.name, locale))

    cat_mgmt_title: str
    if locale == "ru":
        cat_mgmt_title = "📁 Управление категориями"
    elif locale == "es":
        cat_mgmt_title = "📁 Gestión de Categorías"
    else:
        cat_mgmt_title = "📁 Category Management"

    text: str = (
        f"{t('admin_category_created', locale=locale, name=cat_name)}\n\n"
        f"{cat_mgmt_title}"
    )
    keyboard = get_admin_categories_keyboard(
        categories=categories,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()
