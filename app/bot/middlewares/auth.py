from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.models.user import User
from app.database.repositories.user_repo import UserRepo
from app.schemas.user import UserCreateOrUpdateDTO


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user: TelegramUser | None = data.get("event_from_user")
        if telegram_user is None and isinstance(event, (Message, CallbackQuery)):
            telegram_user = event.from_user
        elif telegram_user is None and hasattr(event, "from_user"):
            from_user_val: Any = getattr(event, "from_user", None)
            if isinstance(from_user_val, TelegramUser):
                telegram_user = from_user_val

        if telegram_user is not None and not telegram_user.is_bot:
            session: AsyncSession | None = data.get("session")
            if session is not None:
                user_repo: UserRepo = UserRepo(session)
                user_dto: UserCreateOrUpdateDTO = UserCreateOrUpdateDTO(
                    id=telegram_user.id,
                    username=telegram_user.username,
                    full_name=telegram_user.full_name or telegram_user.first_name,
                    language_code=telegram_user.language_code or "en",
                )
                db_user: User = await user_repo.upsert(user_dto)
                await session.flush()
                data["user"] = db_user
                admin_ids: list[int] = get_settings().admin_user_ids
                data["is_admin"] = db_user.id in admin_ids
            else:
                admin_ids = get_settings().admin_user_ids
                data["user"] = None
                data["is_admin"] = telegram_user.id in admin_ids
        else:
            data["user"] = None
            data["is_admin"] = False

        return await handler(event, data)
