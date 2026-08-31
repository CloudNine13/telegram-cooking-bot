import html

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, Message

from app.bot.keyboards.callbacks import (
    CatalogNavCallback,
    FavoriteToggleCallback,
    RecipeMediaCallback,
    RecipeViewCallback,
    SortToggleCallback,
)
from app.bot.keyboards.catalog import (
    get_recipe_view_keyboard,
    get_recipes_list_keyboard,
    get_subcategories_keyboard,
    get_top_categories_keyboard,
)
from app.core.i18n.helpers import get_localized_text
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.database.models.user import User
from app.schemas.category import CategoryDTO
from app.schemas.common import PaginatedResponse, PaginationParams, SortOrder
from app.schemas.recipe import RecipeDTO
from app.services.category_service import CategoryService
from app.services.media_downloader_service import (
    DownloadedMediaResult,
    MediaDownloaderService,
)
from app.services.pdf_export_service import (
    ExportedPdfResult,
    PdfExportService,
)
from app.services.recipe_service import RecipeService

catalog_router: Router = Router(name="catalog")


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


def _format_recipe_title(
    title_dict: dict[str, str] | None,
    locale: str = DEFAULT_LOCALE,
) -> str:
    if not title_dict:
        return get_localized_text(title_dict, locale)

    ru_title: str | None = title_dict.get("ru")
    en_title: str | None = title_dict.get("en")

    if ru_title and en_title:
        if ru_title == en_title:
            return ru_title
        return f"{ru_title} / {en_title}"

    if ru_title:
        return ru_title

    if en_title:
        return en_title

    return get_localized_text(title_dict, locale)


def _format_recipe_card(
    recipe: RecipeDTO,
    locale: str = DEFAULT_LOCALE,
) -> str:
    raw_title: str = _format_recipe_title(recipe.title, locale)
    title: str = html.escape(raw_title)
    category_name: str = ""
    if recipe.category is not None:
        category_name = html.escape(
            get_localized_text(recipe.category.name, locale),
        )

    ingredients_lines: list[str] = []
    for ing in recipe.ingredients:
        ing_name: str = html.escape(ing.name)
        qty_unit_parts: list[str] = []
        if ing.quantity is not None:
            formatted_qty: str = (
                f"{ing.quantity:g}"
                if isinstance(ing.quantity, float)
                else str(ing.quantity)
            )
            qty_unit_parts.append(html.escape(formatted_qty))
        if ing.unit is not None:
            qty_unit_parts.append(html.escape(ing.unit))

        if qty_unit_parts:
            ingredients_lines.append(f"• {ing_name} - {' '.join(qty_unit_parts)}")
        else:
            ingredients_lines.append(f"• {ing_name}")

    ingredients_str: str = "\n".join(ingredients_lines) if ingredients_lines else "-"
    instructions_str: str = html.escape(recipe.instructions)

    return t(
        "recipe_card",
        locale=locale,
        title=title,
        prep_time=recipe.prep_time_minutes,
        category=category_name,
        ingredients=ingredients_str,
        instructions=instructions_str,
    )


@catalog_router.message(Command("catalog"))
async def handle_catalog_command(
    message: Message,
    category_service: CategoryService,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    top_categories: list[
        CategoryDTO
    ] = await category_service.get_top_level_categories()

    text: str = t("catalog_title", locale=locale)
    keyboard = get_top_categories_keyboard(
        categories=top_categories,
        locale=locale,
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@catalog_router.callback_query(
    CatalogNavCallback.filter(F.category_id == None),
)
async def handle_top_categories_callback(
    callback: CallbackQuery,
    category_service: CategoryService,
    locale: str = DEFAULT_LOCALE,
) -> None:
    top_categories: list[
        CategoryDTO
    ] = await category_service.get_top_level_categories()

    text: str = t("catalog_title", locale=locale)
    keyboard = get_top_categories_keyboard(
        categories=top_categories,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@catalog_router.callback_query(
    CatalogNavCallback.filter(F.category_id != None),
)
async def handle_category_nav_callback(
    callback: CallbackQuery,
    callback_data: CatalogNavCallback,
    category_service: CategoryService,
    recipe_service: RecipeService,
    locale: str = DEFAULT_LOCALE,
) -> None:
    category_id: int = int(callback_data.category_id or 0)

    cat_name: str
    paginated_recipes: PaginatedResponse[RecipeDTO]

    if category_id == 0:
        cat_name = t("cat_all", locale=locale)
        paginated_recipes = await recipe_service.list_by_category(
            category_id=None,
            sort_order=callback_data.sort_order,
            pagination=PaginationParams(
                page=callback_data.page,
                page_size=5,
            ),
            include_subcategories=True,
        )
    else:
        parent_category: CategoryDTO | None = await category_service.get_category_by_id(
            category_id,
        )
        if parent_category is None:
            await callback.answer(t("category_empty", locale=locale))
            return

        subcategories: list[CategoryDTO] = await category_service.get_subcategories(
            category_id,
        )
        if subcategories and callback_data.parent_id is None:
            text: str = t("subcategory_select", locale=locale)
            keyboard = get_subcategories_keyboard(
                parent=parent_category,
                subcategories=subcategories,
                locale=locale,
            )
            if callback.message is not None:
                await _edit_or_resend_message(
                    message=callback.message,
                    text=text,
                    reply_markup=keyboard,
                )
            await callback.answer()
            return

        paginated_recipes = await recipe_service.list_by_category(
            category_id=category_id,
            sort_order=callback_data.sort_order,
            pagination=PaginationParams(
                page=callback_data.page,
                page_size=5,
            ),
            include_subcategories=True,
        )
        cat_name = html.escape(get_localized_text(parent_category.name, locale))

    if paginated_recipes.total_count == 0:
        empty_text: str = f"📂 <b>{cat_name}</b>\n\n" + t(
            "category_empty",
            locale=locale,
        )
        empty_keyboard = get_recipes_list_keyboard(
            recipes=[],
            category_id=category_id,
            current_page=1,
            total_pages=1,
            sort_order=callback_data.sort_order,
            locale=locale,
            parent_id=callback_data.parent_id,
        )
        if callback.message is not None:
            await _edit_or_resend_message(
                message=callback.message,
                text=empty_text,
                reply_markup=empty_keyboard,
            )
        await callback.answer()
        return

    sort_label: str = (
        t("sort_alpha_active", locale=locale)
        if callback_data.sort_order == SortOrder.ALPHABETICAL
        else t("sort_date_active", locale=locale)
    )
    header_text: str = f"📂 <b>{cat_name}</b>\n{sort_label}\n"
    list_keyboard = get_recipes_list_keyboard(
        recipes=paginated_recipes.items,
        category_id=category_id,
        current_page=paginated_recipes.page,
        total_pages=paginated_recipes.total_pages,
        sort_order=callback_data.sort_order,
        locale=locale,
        parent_id=callback_data.parent_id,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=header_text,
            reply_markup=list_keyboard,
        )
    await callback.answer()


@catalog_router.callback_query(SortToggleCallback.filter())
async def handle_sort_toggle_callback(
    callback: CallbackQuery,
    callback_data: SortToggleCallback,
    category_service: CategoryService,
    recipe_service: RecipeService,
    locale: str = DEFAULT_LOCALE,
) -> None:
    category_id: int = callback_data.category_id

    cat_name: str
    paginated_recipes: PaginatedResponse[RecipeDTO]

    if category_id == 0:
        cat_name = t("cat_all", locale=locale)
        paginated_recipes = await recipe_service.list_by_category(
            category_id=None,
            sort_order=callback_data.current_sort,
            pagination=PaginationParams(
                page=1,
                page_size=5,
            ),
            include_subcategories=True,
        )
    else:
        category: CategoryDTO | None = await category_service.get_category_by_id(
            category_id,
        )
        cat_name = (
            html.escape(get_localized_text(category.name, locale))
            if category is not None
            else ""
        )
        paginated_recipes = await recipe_service.list_by_category(
            category_id=category_id,
            sort_order=callback_data.current_sort,
            pagination=PaginationParams(
                page=1,
                page_size=5,
            ),
            include_subcategories=True,
        )

    sort_label: str = (
        t("sort_alpha_active", locale=locale)
        if callback_data.current_sort == SortOrder.ALPHABETICAL
        else t("sort_date_active", locale=locale)
    )
    header_text: str = f"📂 <b>{cat_name}</b>\n{sort_label}\n"
    list_keyboard = get_recipes_list_keyboard(
        recipes=paginated_recipes.items,
        category_id=category_id,
        current_page=paginated_recipes.page,
        total_pages=paginated_recipes.total_pages,
        sort_order=callback_data.current_sort,
        locale=locale,
        parent_id=callback_data.parent_id,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=header_text,
            reply_markup=list_keyboard,
        )
    await callback.answer()


@catalog_router.callback_query(RecipeViewCallback.filter())
async def handle_recipe_view_callback(
    callback: CallbackQuery,
    callback_data: RecipeViewCallback,
    recipe_service: RecipeService,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
    is_admin: bool = False,
) -> None:
    recipe: RecipeDTO | None = await recipe_service.get_recipe(
        callback_data.recipe_id,
    )

    if recipe is None:
        await callback.answer(
            text=t("recipe_not_found", locale=locale),
            show_alert=True,
        )
        return

    user_id: int = user.id if user is not None else 0
    is_favorite: bool = await recipe_service.is_favorite(
        user_id=user_id,
        recipe_id=recipe.id,
    )

    card_text: str = _format_recipe_card(recipe=recipe, locale=locale)
    view_keyboard = get_recipe_view_keyboard(
        recipe=recipe,
        is_favorite=is_favorite,
        locale=locale,
        source=callback_data.source,
        category_id=callback_data.category_id,
        page=callback_data.page,
        is_admin=is_admin,
    )

    if callback.message is not None:
        if recipe.photo_file_id:
            try:
                await callback.message.delete()
            except TelegramBadRequest:
                pass
            await callback.message.answer_photo(
                photo=recipe.photo_file_id,
                caption=card_text,
                reply_markup=view_keyboard,
            )
        else:
            await _edit_or_resend_message(
                message=callback.message,
                text=card_text,
                reply_markup=view_keyboard,
            )
    await callback.answer()


@catalog_router.callback_query(RecipeMediaCallback.filter())
async def handle_recipe_media_callback(
    callback: CallbackQuery,
    callback_data: RecipeMediaCallback,
    recipe_service: RecipeService,
    pdf_export_service: PdfExportService,
    media_downloader_service: MediaDownloaderService,
    locale: str = DEFAULT_LOCALE,
) -> None:
    recipe: RecipeDTO | None = await recipe_service.get_recipe(
        callback_data.recipe_id,
    )

    if recipe is None or callback.message is None:
        await callback.answer(
            text=t("recipe_not_found", locale=locale),
            show_alert=True,
        )
        return

    title: str = html.escape(get_localized_text(recipe.title, locale))

    if callback_data.media_type == "pdf":
        if recipe.document_file_id:
            await callback.message.answer_document(
                document=recipe.document_file_id,
                caption=t("recipe_pdf_caption", locale=locale, title=title),
            )
            await callback.answer()
            return

        pdf_res: ExportedPdfResult | None = await pdf_export_service.recipe_to_pdf(
            recipe=recipe,
            locale=locale,
        )
        if pdf_res is not None:
            input_file: FSInputFile = FSInputFile(
                path=str(pdf_res.file_path),
                filename=pdf_res.filename,
            )
            await callback.message.answer_document(
                document=input_file,
                caption=t("recipe_pdf_caption", locale=locale, title=title),
            )
            await pdf_export_service.cleanup(pdf_res.file_path)
            await callback.answer()
            return

    elif callback_data.media_type == "video":
        if recipe.video_file_id:
            await callback.message.answer_video(
                video=recipe.video_file_id,
                caption=t("recipe_video_caption", locale=locale, title=title),
            )
            await callback.answer()
            return

        if recipe.instagram_url:
            media_res: (
                DownloadedMediaResult | None
            ) = await media_downloader_service.download_video(
                url=recipe.instagram_url,
            )
            if media_res is not None:
                video_file: FSInputFile = FSInputFile(
                    path=str(media_res.file_path),
                    filename=media_res.filename,
                )
                await callback.message.answer_video(
                    video=video_file,
                    caption=t(
                        "recipe_video_caption",
                        locale=locale,
                        title=title,
                    ),
                )
                await media_downloader_service.cleanup(media_res.file_path)
                await callback.answer()
                return

    await callback.answer(text=t("error_occurred", locale=locale))


@catalog_router.callback_query(FavoriteToggleCallback.filter())
async def handle_favorite_toggle_callback(
    callback: CallbackQuery,
    callback_data: FavoriteToggleCallback,
    recipe_service: RecipeService,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
    is_admin: bool = False,
) -> None:
    if user is None:
        await callback.answer()
        return

    recipe: RecipeDTO | None = await recipe_service.get_recipe(
        callback_data.recipe_id,
    )

    if recipe is None:
        await callback.answer(
            text=t("recipe_not_found", locale=locale),
            show_alert=True,
        )
        return

    is_favorite: bool = await recipe_service.toggle_favorite(
        user_id=user.id,
        recipe_id=recipe.id,
    )

    alert_msg: str = (
        t("favorite_added", locale=locale)
        if is_favorite
        else t("favorite_removed", locale=locale)
    )
    await callback.answer(text=alert_msg, show_alert=False)

    view_keyboard = get_recipe_view_keyboard(
        recipe=recipe,
        is_favorite=is_favorite,
        locale=locale,
        source=callback_data.source,
        category_id=callback_data.category_id,
        page=callback_data.page,
        is_admin=is_admin,
    )

    if callback.message is not None:
        if callback.message.caption:
            await callback.message.edit_reply_markup(
                reply_markup=view_keyboard,
            )
        else:
            await callback.message.edit_reply_markup(
                reply_markup=view_keyboard,
            )
