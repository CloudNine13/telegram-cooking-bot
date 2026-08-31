from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.callbacks import (
    LanguageSelectCallback,
    MainMenuCallback,
)
from app.bot.keyboards.common import (
    get_language_keyboard,
    get_main_menu_keyboard,
    get_search_menu_keyboard,
)
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.database.models.user import User
from app.database.repositories.user_repo import UserRepo

common_router: Router = Router(name="common")


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


@common_router.message(CommandStart())
async def handle_start(
    message: Message,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
    is_admin: bool = False,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    welcome_text: str = t("welcome", locale=locale)
    keyboard = get_main_menu_keyboard(locale=locale, is_admin=is_admin)

    await message.answer(
        text=welcome_text,
        reply_markup=keyboard,
    )


@common_router.message(Command("help"))
async def handle_help(
    message: Message,
    locale: str = DEFAULT_LOCALE,
    is_admin: bool = False,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    help_text: str = t("help", locale=locale)
    if is_admin:
        help_text += t("help_admin", locale=locale)

    keyboard = get_main_menu_keyboard(locale=locale, is_admin=is_admin)

    await message.answer(
        text=help_text,
        reply_markup=keyboard,
    )


@common_router.message(Command("language"))
async def handle_language_command(
    message: Message,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    prompt_text: str = t("choose_language", locale=locale)
    keyboard = get_language_keyboard(locale=locale)

    await message.answer(
        text=prompt_text,
        reply_markup=keyboard,
    )


@common_router.callback_query(MainMenuCallback.filter(F.target == "main"))
async def handle_main_menu_callback(
    callback: CallbackQuery,
    locale: str = DEFAULT_LOCALE,
    is_admin: bool = False,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    text: str = t("main_menu", locale=locale)
    keyboard = get_main_menu_keyboard(locale=locale, is_admin=is_admin)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@common_router.callback_query(MainMenuCallback.filter(F.target == "language"))
async def handle_language_callback(
    callback: CallbackQuery,
    locale: str = DEFAULT_LOCALE,
) -> None:
    text: str = t("choose_language", locale=locale)
    keyboard = get_language_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@common_router.callback_query(MainMenuCallback.filter(F.target == "search"))
async def handle_search_menu_callback(
    callback: CallbackQuery,
    locale: str = DEFAULT_LOCALE,
) -> None:
    text: str = t("search_menu_title", locale=locale)
    keyboard = get_search_menu_keyboard(locale=locale)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=text,
            reply_markup=keyboard,
        )
    await callback.answer()


@common_router.callback_query(LanguageSelectCallback.filter())
async def handle_language_select(
    callback: CallbackQuery,
    callback_data: LanguageSelectCallback,
    session: AsyncSession,
    user: User | None = None,
    is_admin: bool = False,
) -> None:
    new_locale: str = callback_data.language_code
    if user is not None:
        user_repo: UserRepo = UserRepo(session)
        await user_repo.update_language(user.id, new_locale)

    updated_text: str = t("language_updated", locale=new_locale)
    menu_keyboard = get_main_menu_keyboard(locale=new_locale, is_admin=is_admin)

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=updated_text,
            reply_markup=menu_keyboard,
        )
    await callback.answer()
