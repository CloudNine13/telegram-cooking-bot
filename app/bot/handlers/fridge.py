import html

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.keyboards.callbacks import FridgeActionCallback
from app.bot.keyboards.fridge import (
    get_fridge_cancel_keyboard,
    get_fridge_main_keyboard,
    get_fridge_match_results_keyboard,
)
from app.bot.states.fridge import FridgeInputState
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.database.models.user import User
from app.schemas.fridge import FridgeItemDTO, RecipeMatchResultDTO
from app.services.fridge_matcher_service import FridgeMatcherService
from app.services.fridge_service import FridgeService

fridge_router: Router = Router(name="fridge")


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


def _render_fridge_view(
    items: list[FridgeItemDTO],
    locale: str = DEFAULT_LOCALE,
) -> tuple[str, InlineKeyboardMarkup]:
    if not items:
        text: str = (
            f"{t('fridge_title', locale=locale)}\n\n{t('fridge_empty', locale=locale)}"
        )
        keyboard = get_fridge_main_keyboard(items_count=0, locale=locale)
        return text, keyboard

    items_list_str: str = "\n".join(
        [f"• {html.escape(item.raw_name)}" for item in items],
    )
    text = (
        f"{t('fridge_title', locale=locale)}\n\n"
        f"{t('fridge_items_list', locale=locale, count=len(items), items=items_list_str)}"
    )
    keyboard = get_fridge_main_keyboard(items_count=len(items), locale=locale)

    return text, keyboard


@fridge_router.message(Command("fridge"))
async def handle_fridge_command(
    message: Message,
    fridge_service: FridgeService,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    user_id: int = user.id if user is not None else 0
    items: list[FridgeItemDTO] = await fridge_service.get_user_items(user_id)

    text, keyboard = _render_fridge_view(items=items, locale=locale)
    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@fridge_router.callback_query(FridgeActionCallback.filter(F.action == "view"))
async def handle_fridge_view_callback(
    callback: CallbackQuery,
    fridge_service: FridgeService,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    user_id: int = user.id if user is not None else 0
    items: list[FridgeItemDTO] = await fridge_service.get_user_items(user_id)

    text, keyboard = _render_fridge_view(items=items, locale=locale)
    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@fridge_router.callback_query(FridgeActionCallback.filter(F.action == "add"))
async def handle_fridge_add_callback(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.set_state(FridgeInputState.waiting_for_items_add)
    text: str = t("fridge_input_add_prompt", locale=locale)
    keyboard = get_fridge_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@fridge_router.callback_query(
    FridgeActionCallback.filter(F.action == "replace"),
)
async def handle_fridge_replace_callback(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.set_state(FridgeInputState.waiting_for_items_replace)
    text: str = t("fridge_input_replace_prompt", locale=locale)
    keyboard = get_fridge_cancel_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@fridge_router.callback_query(FridgeActionCallback.filter(F.action == "clear"))
async def handle_fridge_clear_callback(
    callback: CallbackQuery,
    fridge_service: FridgeService,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
) -> None:
    user_id: int = user.id if user is not None else 0
    await fridge_service.clear_fridge(user_id)

    text: str = (
        f"{t('fridge_cleared', locale=locale)}\n\n{t('fridge_empty', locale=locale)}"
    )
    keyboard = get_fridge_main_keyboard(items_count=0, locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@fridge_router.callback_query(FridgeActionCallback.filter(F.action == "cancel"))
async def handle_fridge_cancel_callback(
    callback: CallbackQuery,
    fridge_service: FridgeService,
    state: FSMContext,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
) -> None:
    await state.clear()
    user_id: int = user.id if user is not None else 0
    items: list[FridgeItemDTO] = await fridge_service.get_user_items(user_id)

    text, keyboard = _render_fridge_view(items=items, locale=locale)
    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@fridge_router.callback_query(
    FridgeActionCallback.filter(F.action == "match_full"),
)
async def handle_fridge_match_full_callback(
    callback: CallbackQuery,
    fridge_matcher_service: FridgeMatcherService,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
) -> None:
    user_id: int = user.id if user is not None else 0
    matches: list[
        RecipeMatchResultDTO
    ] = await fridge_matcher_service.find_full_matches(
        user_id=user_id,
        locale=locale,
    )

    if not matches:
        text: str = t("fridge_match_full_empty", locale=locale)
        keyboard = get_fridge_match_results_keyboard(
            matches=[],
            match_type="full",
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

    text = t("fridge_match_full_title", locale=locale)
    keyboard = get_fridge_match_results_keyboard(
        matches=matches,
        match_type="full",
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@fridge_router.callback_query(
    FridgeActionCallback.filter(F.action == "match_partial"),
)
async def handle_fridge_match_partial_callback(
    callback: CallbackQuery,
    fridge_matcher_service: FridgeMatcherService,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
) -> None:
    user_id: int = user.id if user is not None else 0
    matches: list[
        RecipeMatchResultDTO
    ] = await fridge_matcher_service.find_partial_matches(
        user_id=user_id,
        max_missing=2,
        locale=locale,
    )

    if not matches:
        text: str = t("fridge_match_partial_empty", locale=locale)
        keyboard = get_fridge_match_results_keyboard(
            matches=[],
            match_type="partial",
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

    text = t("fridge_match_partial_title", locale=locale)
    keyboard = get_fridge_match_results_keyboard(
        matches=matches,
        match_type="partial",
        locale=locale,
    )

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@fridge_router.message(FridgeInputState.waiting_for_items_add)
async def handle_fridge_add_input(
    message: Message,
    fridge_service: FridgeService,
    state: FSMContext,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
) -> None:
    raw_text: str = (message.text or "").strip()
    if not raw_text:
        await state.clear()
        return

    user_id: int = user.id if user is not None else 0
    added: list[FridgeItemDTO] = await fridge_service.add_ingredients(
        user_id,
        raw_text,
    )
    await state.clear()

    items: list[FridgeItemDTO] = await fridge_service.get_user_items(user_id)
    added_count_msg: str = t("fridge_added", locale=locale, count=len(added))
    text, keyboard = _render_fridge_view(items=items, locale=locale)

    await message.answer(
        text=f"{added_count_msg}\n\n{text}",
        reply_markup=keyboard,
    )


@fridge_router.message(FridgeInputState.waiting_for_items_replace)
async def handle_fridge_replace_input(
    message: Message,
    fridge_service: FridgeService,
    state: FSMContext,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
) -> None:
    raw_text: str = (message.text or "").strip()
    if not raw_text:
        await state.clear()
        return

    user_id: int = user.id if user is not None else 0
    replaced: list[FridgeItemDTO] = await fridge_service.replace_ingredients(
        user_id,
        raw_text,
    )
    await state.clear()

    items: list[FridgeItemDTO] = await fridge_service.get_user_items(user_id)
    replaced_count_msg: str = t(
        "fridge_replaced",
        locale=locale,
        count=len(replaced),
    )
    text, keyboard = _render_fridge_view(items=items, locale=locale)

    await message.answer(
        text=f"{replaced_count_msg}\n\n{text}",
        reply_markup=keyboard,
    )
