from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

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


def _format_recipe_card(
    recipe: RecipeDTO,
    locale: str = DEFAULT_LOCALE,
) -> str:
    title: str = (
        recipe.title_ru if locale == "ru" and recipe.title_ru else recipe.title_en
    )
    category_name: str = ""
    if recipe.category is not None:
        category_name = (
            recipe.category.name_ru
            if locale == "ru" and recipe.category.name_ru
            else recipe.category.name_en
        )

    ingredients_lines: list[str] = []
    for ing in recipe.ingredients:
        ing_name: str = ing.name_ru if locale == "ru" and ing.name_ru else ing.name_en
        qty_unit_parts: list[str] = []
        if ing.quantity is not None:
            formatted_qty: str = (
                f"{ing.quantity:g}"
                if isinstance(ing.quantity, float)
                else str(ing.quantity)
            )
            qty_unit_parts.append(formatted_qty)
        if ing.unit is not None:
            qty_unit_parts.append(ing.unit)

        if qty_unit_parts:
            ingredients_lines.append(f"• {ing_name} - {' '.join(qty_unit_parts)}")
        else:
            ingredients_lines.append(f"• {ing_name}")

    ingredients_str: str = "\n".join(ingredients_lines) if ingredients_lines else "-"
    instructions_str: str = (
        recipe.instructions_ru
        if locale == "ru" and recipe.instructions_ru
        else recipe.instructions_en
    )

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
    session: AsyncSession,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    category_service: CategoryService = CategoryService(session=session)
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
    session: AsyncSession,
    locale: str = DEFAULT_LOCALE,
) -> None:
    category_service: CategoryService = CategoryService(session=session)
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
    session: AsyncSession,
    locale: str = DEFAULT_LOCALE,
) -> None:
    category_id: int = int(callback_data.category_id or 1)
    category_service: CategoryService = CategoryService(session=session)
    recipe_service: RecipeService = RecipeService(session=session)

    parent_category: CategoryDTO | None = await category_service.get_category_by_id(
        category_id
    )
    if parent_category is None:
        await callback.answer(t("category_empty", locale=locale))
        return

    subcategories: list[CategoryDTO] = await category_service.get_subcategories(
        category_id
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

    paginated_recipes: PaginatedResponse[
        RecipeDTO
    ] = await recipe_service.list_by_category(
        category_id=category_id,
        sort_order=callback_data.sort_order,
        pagination=PaginationParams(
            page=callback_data.page,
            page_size=5,
        ),
        include_subcategories=True,
    )

    cat_name: str = (
        parent_category.name_ru if locale == "ru" else parent_category.name_en
    )

    if paginated_recipes.total_count == 0:
        empty_text: str = f"📂 *{cat_name}*\n\n" + t(
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
    header_text: str = f"📂 *{cat_name}*\n{sort_label}\n"
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
    session: AsyncSession,
    locale: str = DEFAULT_LOCALE,
) -> None:
    category_id: int = callback_data.category_id
    category_service: CategoryService = CategoryService(session=session)
    recipe_service: RecipeService = RecipeService(session=session)

    category: CategoryDTO | None = await category_service.get_category_by_id(
        category_id,
    )
    cat_name: str = ""
    if category is not None:
        cat_name = category.name_ru if locale == "ru" else category.name_en

    paginated_recipes: PaginatedResponse[
        RecipeDTO
    ] = await recipe_service.list_by_category(
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
    header_text: str = f"📂 *{cat_name}*\n{sort_label}\n"
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
    session: AsyncSession,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
) -> None:
    recipe_service: RecipeService = RecipeService(session=session)
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
    session: AsyncSession,
    locale: str = DEFAULT_LOCALE,
) -> None:
    recipe_service: RecipeService = RecipeService(session=session)
    recipe: RecipeDTO | None = await recipe_service.get_recipe(
        callback_data.recipe_id,
    )

    if recipe is None or callback.message is None:
        await callback.answer(
            text=t("recipe_not_found", locale=locale),
            show_alert=True,
        )
        return

    title: str = (
        recipe.title_ru if locale == "ru" and recipe.title_ru else recipe.title_en
    )

    if callback_data.media_type == "pdf":
        if recipe.document_file_id:
            await callback.message.answer_document(
                document=recipe.document_file_id,
                caption=t("recipe_pdf_caption", locale=locale, title=title),
            )
            await callback.answer()
            return

        pdf_service: PdfExportService = PdfExportService()
        pdf_res: ExportedPdfResult | None = await pdf_service.recipe_to_pdf(
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
            pdf_service.cleanup(pdf_res.file_path)
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
            downloader: MediaDownloaderService = MediaDownloaderService()
            media_res: DownloadedMediaResult | None = await downloader.download_video(
                url=recipe.instagram_url
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
                downloader.cleanup(media_res.file_path)
                await callback.answer()
                return

    await callback.answer(text=t("error_occurred", locale=locale))


@catalog_router.callback_query(FavoriteToggleCallback.filter())
async def handle_favorite_toggle_callback(
    callback: CallbackQuery,
    callback_data: FavoriteToggleCallback,
    session: AsyncSession,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
) -> None:
    if user is None:
        await callback.answer()
        return

    recipe_service: RecipeService = RecipeService(session=session)
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
    await session.commit()

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
