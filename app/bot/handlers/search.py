import html

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.keyboards.callbacks import (
    CategorySearchCallback,
    PaginationCallback,
    SearchModeCallback,
)
from app.bot.keyboards.catalog import get_search_results_keyboard
from app.bot.keyboards.common import (
    get_cancel_keyboard,
    get_search_menu_keyboard,
)
from app.bot.keyboards.fridge import get_fridge_match_results_keyboard
from app.bot.states.search import CategorySearchState, GlobalSearchState
from app.core.i18n.helpers import get_localized_text
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.schemas.category import CategoryDTO
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.fridge import RecipeMatchResultDTO
from app.schemas.recipe import RecipeDTO
from app.services.category_service import CategoryService
from app.services.fridge_matcher_service import FridgeMatcherService
from app.services.recipe_service import RecipeService

search_router: Router = Router(name="search")


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


@search_router.message(Command("search"))
async def handle_search_command(
    message: Message,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    text: str = t("search_menu_title", locale=locale)
    keyboard = get_search_menu_keyboard(locale=locale)

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@search_router.callback_query(SearchModeCallback.filter(F.mode == "menu"))
async def handle_search_mode_menu(
    callback: CallbackQuery,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    text: str = t("search_menu_title", locale=locale)
    keyboard = get_search_menu_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@search_router.callback_query(SearchModeCallback.filter(F.mode == "global"))
async def handle_search_mode_global(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.set_state(GlobalSearchState.waiting_for_query)
    text: str = t("search_prompt", locale=locale)
    keyboard = get_cancel_keyboard(locale=locale, target="search")

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@search_router.callback_query(SearchModeCallback.filter(F.mode == "instant"))
async def handle_search_mode_instant(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.set_state(GlobalSearchState.waiting_for_ingredients)
    text: str = t("search_instant_prompt", locale=locale)
    keyboard = get_cancel_keyboard(locale=locale, target="search")

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@search_router.callback_query(CategorySearchCallback.filter())
async def handle_category_search_callback(
    callback: CallbackQuery,
    callback_data: CategorySearchCallback,
    category_service: CategoryService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    cat_name: str
    if callback_data.category_id == 0:
        cat_name = t("cat_all", locale=locale)
    else:
        category: CategoryDTO | None = await category_service.get_category_by_id(
            callback_data.category_id,
        )
        cat_name = (
            get_localized_text(category.name, locale=locale)
            if category is not None
            else ""
        )

    await state.set_state(CategorySearchState.waiting_for_query)
    await state.update_data(
        category_id=callback_data.category_id,
        category_name=cat_name,
    )

    text: str = t(
        "search_in_category_prompt",
        locale=locale,
        category=html.escape(cat_name),
    )
    keyboard = get_cancel_keyboard(locale=locale, target="search")

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@search_router.message(CategorySearchState.waiting_for_query)
async def handle_category_search_query(
    message: Message,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    query_text: str = (message.text or "").strip()
    state_data = await state.get_data()
    category_id: int | None = state_data.get("category_id")

    if not query_text or category_id is None:
        await state.clear()
        return

    paginated: PaginatedResponse[RecipeDTO]

    if category_id == 0:
        paginated = await recipe_service.search_global(
            query_text=query_text,
            pagination=PaginationParams(page=1, page_size=5),
        )
    else:
        paginated = await recipe_service.search_in_category(
            category_id=category_id,
            query_text=query_text,
            pagination=PaginationParams(page=1, page_size=5),
        )

    await state.update_data(
        query_text=query_text,
        search_type="category",
        category_id=category_id,
    )

    query_escaped: str = html.escape(query_text)

    if paginated.total_count == 0:
        await message.answer(
            text=t("search_no_results", locale=locale, query=query_escaped),
            reply_markup=get_cancel_keyboard(locale=locale, target="search"),
        )
        return

    results_text: str = t(
        "search_results",
        locale=locale,
        count=paginated.total_count,
        query=query_escaped,
    )
    keyboard = get_search_results_keyboard(
        recipes=paginated.items,
        current_page=paginated.page,
        total_pages=paginated.total_pages,
        locale=locale,
    )

    await message.answer(
        text=results_text,
        reply_markup=keyboard,
    )


@search_router.message(GlobalSearchState.waiting_for_query)
async def handle_global_search_query(
    message: Message,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    query_text: str = (message.text or "").strip()
    if not query_text:
        await state.clear()
        return

    paginated: PaginatedResponse[RecipeDTO] = await recipe_service.search_global(
        query_text=query_text,
        pagination=PaginationParams(page=1, page_size=5),
    )

    await state.update_data(
        query_text=query_text,
        search_type="global",
    )

    query_escaped: str = html.escape(query_text)

    if paginated.total_count == 0:
        await message.answer(
            text=t("search_no_results", locale=locale, query=query_escaped),
            reply_markup=get_cancel_keyboard(locale=locale, target="search"),
        )
        return

    results_text: str = t(
        "search_results",
        locale=locale,
        count=paginated.total_count,
        query=query_escaped,
    )
    keyboard = get_search_results_keyboard(
        recipes=paginated.items,
        current_page=paginated.page,
        total_pages=paginated.total_pages,
        locale=locale,
    )

    await message.answer(
        text=results_text,
        reply_markup=keyboard,
    )


@search_router.message(GlobalSearchState.waiting_for_ingredients)
async def handle_instant_ingredient_search(
    message: Message,
    fridge_matcher_service: FridgeMatcherService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    raw_ingredients: str = (message.text or "").strip()
    if not raw_ingredients:
        await state.clear()
        return

    await state.clear()
    matches: list[
        RecipeMatchResultDTO
    ] = await fridge_matcher_service.search_by_ingredients(
        raw_ingredients_text=raw_ingredients,
        max_missing=2,
        locale=locale,
    )

    if not matches:
        await message.answer(
            text=t("search_instant_no_results", locale=locale),
            reply_markup=get_cancel_keyboard(locale=locale, target="search"),
        )
        return

    results_text: str = t(
        "search_instant_results",
        locale=locale,
        count=len(matches),
    )
    keyboard = get_fridge_match_results_keyboard(
        matches=matches,
        match_type="instant",
        locale=locale,
    )

    await message.answer(
        text=results_text,
        reply_markup=keyboard,
    )


@search_router.callback_query(PaginationCallback.filter(F.target == "search"))
async def handle_search_pagination(
    callback: CallbackQuery,
    callback_data: PaginationCallback,
    recipe_service: RecipeService,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    state_data = await state.get_data()
    query_text: str = state_data.get("query_text", "")
    search_type: str = state_data.get("search_type", "global")
    category_id: int | None = state_data.get("category_id")

    if not query_text:
        await callback.answer()
        return

    paginated: PaginatedResponse[RecipeDTO]

    if search_type == "category" and category_id is not None and category_id != 0:
        paginated = await recipe_service.search_in_category(
            category_id=category_id,
            query_text=query_text,
            pagination=PaginationParams(
                page=callback_data.page,
                page_size=5,
            ),
        )
    else:
        paginated = await recipe_service.search_global(
            query_text=query_text,
            pagination=PaginationParams(
                page=callback_data.page,
                page_size=5,
            ),
        )

    query_escaped: str = html.escape(query_text)
    results_text: str = t(
        "search_results",
        locale=locale,
        count=paginated.total_count,
        query=query_escaped,
    )
    keyboard = get_search_results_keyboard(
        recipes=paginated.items,
        current_page=paginated.page,
        total_pages=paginated.total_pages,
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=results_text,
            reply_markup=keyboard,
        )
    await callback.answer()
