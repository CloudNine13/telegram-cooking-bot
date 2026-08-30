from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.callbacks import PaginationCallback
from app.bot.keyboards.common import get_back_keyboard
from app.bot.keyboards.favorites import get_favorites_keyboard
from app.core.i18n.locales import DEFAULT_LOCALE
from app.core.i18n.translator import t
from app.database.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.recipe import RecipeDTO
from app.services.recipe_service import RecipeService

favorites_router: Router = Router(name="favorites")


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


@favorites_router.message(Command("favorites"))
async def handle_favorites_command(
    message: Message,
    session: AsyncSession,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()

    user_id: int = user.id if user is not None else 0
    recipe_service: RecipeService = RecipeService(session=session)
    paginated: PaginatedResponse[RecipeDTO] = await recipe_service.get_user_favorites(
        user_id=user_id,
        pagination=PaginationParams(page=1, page_size=5),
    )

    if paginated.total_count == 0:
        await message.answer(
            text=f"{t('favorites_title', locale=locale)}\n\n{t('favorites_empty', locale=locale)}",
            reply_markup=get_back_keyboard(target="main", locale=locale),
        )
        return

    await message.answer(
        text=t("favorites_title", locale=locale),
        reply_markup=get_favorites_keyboard(
            recipes=paginated.items,
            current_page=paginated.page,
            total_pages=paginated.total_pages,
            locale=locale,
        ),
    )


@favorites_router.callback_query(
    PaginationCallback.filter(F.target == "favorites"),
)
async def handle_favorites_pagination(
    callback: CallbackQuery,
    callback_data: PaginationCallback,
    session: AsyncSession,
    user: User | None = None,
    locale: str = DEFAULT_LOCALE,
) -> None:
    user_id: int = user.id if user is not None else 0
    recipe_service: RecipeService = RecipeService(session=session)
    paginated: PaginatedResponse[RecipeDTO] = await recipe_service.get_user_favorites(
        user_id=user_id,
        pagination=PaginationParams(page=callback_data.page, page_size=5),
    )

    if paginated.total_count == 0:
        if callback.message is not None:
            await _edit_or_resend_message(
                message=callback.message,
                text=f"{t('favorites_title', locale=locale)}\n\n{t('favorites_empty', locale=locale)}",
                reply_markup=get_back_keyboard(target="main", locale=locale),
            )
        await callback.answer()
        return

    if callback.message is not None:
        await _edit_or_resend_message(
            message=callback.message,
            text=t("favorites_title", locale=locale),
            reply_markup=get_favorites_keyboard(
                recipes=paginated.items,
                current_page=paginated.page,
                total_pages=paginated.total_pages,
                locale=locale,
            ),
        )
    await callback.answer()
