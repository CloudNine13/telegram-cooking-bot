from aiogram import Router

from app.bot.handlers.admin import admin_router
from app.bot.handlers.catalog import catalog_router
from app.bot.handlers.common import common_router
from app.bot.handlers.favorites import favorites_router
from app.bot.handlers.fridge import fridge_router
from app.bot.handlers.search import search_router

main_router: Router = Router(name="main_router")
main_router.include_router(admin_router)
main_router.include_router(common_router)
main_router.include_router(catalog_router)
main_router.include_router(search_router)
main_router.include_router(fridge_router)
main_router.include_router(favorites_router)

__all__: list[str] = [
    "admin_router",
    "catalog_router",
    "common_router",
    "favorites_router",
    "fridge_router",
    "main_router",
    "search_router",
]
