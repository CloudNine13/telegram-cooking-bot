from typing import Any

from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser

from app.core.config import get_settings


class IsAdminFilter(Filter):
    def __init__(self, admin_user_ids: list[int] | None = None) -> None:
        self.admin_user_ids: list[int] | None = admin_user_ids

    async def __call__(
        self,
        event: TelegramObject,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        if self.admin_user_ids is not None:
            configured_ids: list[int] = self.admin_user_ids
        else:
            injected_admin: Any = kwargs.get("is_admin")
            if isinstance(injected_admin, bool):
                return injected_admin

            configured_ids = get_settings().admin_user_ids

        user_id: int | None = None

        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id
        elif hasattr(event, "from_user"):
            from_user_val: Any = getattr(event, "from_user", None)
            if isinstance(from_user_val, TelegramUser):
                user_id = from_user_val.id
        elif "event_from_user" in kwargs:
            from_user: TelegramUser | None = kwargs.get("event_from_user")
            if from_user is not None:
                user_id = from_user.id

        if user_id is None:
            return False

        return user_id in configured_ids
