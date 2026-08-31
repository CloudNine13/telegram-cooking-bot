from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser

from app.core.i18n.locales import DEFAULT_LOCALE, SUPPORTED_LOCALES
from app.database.models.user import User


class UserI18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        locale: str = DEFAULT_LOCALE

        db_user: User | None = data.get("user")
        if db_user is not None and db_user.language_code:
            locale = db_user.language_code
        else:
            telegram_user: TelegramUser | None = data.get("event_from_user")
            if telegram_user is not None and telegram_user.language_code:
                raw_lang: str = telegram_user.language_code.lower()
                locale = raw_lang[:2]

        if locale not in SUPPORTED_LOCALES:
            locale = DEFAULT_LOCALE

        data["locale"] = locale

        return await handler(event, data)
