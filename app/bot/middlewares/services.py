from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.category_service import CategoryService
from app.services.fridge_matcher_service import FridgeMatcherService
from app.services.fridge_service import FridgeService
from app.services.media_downloader_service import MediaDownloaderService
from app.services.pdf_export_service import PdfExportService
from app.services.recipe_service import RecipeService


class ServicesMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session: AsyncSession | None = data.get("session")
        if session is not None:
            data["category_service"] = CategoryService(session=session)
            data["recipe_service"] = RecipeService(session=session)
            data["fridge_service"] = FridgeService(session=session)
            data["fridge_matcher_service"] = FridgeMatcherService(
                session=session,
            )

        data["media_downloader_service"] = MediaDownloaderService()
        data["pdf_export_service"] = PdfExportService()

        return await handler(event, data)
