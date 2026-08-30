import asyncio
import logging
import pathlib
import sys

project_root: str = str(pathlib.Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.bot.handlers import main_router
from app.bot.middlewares import (
    AuthMiddleware,
    DbSessionMiddleware,
    ServicesMiddleware,
    UserI18nMiddleware,
)
from app.core.config import Settings, get_settings
from app.core.seeder import seed_initial_categories
from app.database.session import (
    get_async_engine,
    get_session_maker,
)


async def create_fsm_storage(redis_url: str) -> BaseStorage:
    try:
        redis_client: Redis = Redis.from_url(
            redis_url,
            decode_responses=False,
        )
        await redis_client.ping()

        return RedisStorage(redis=redis_client)
    except (RedisError, ConnectionError, OSError):
        return MemoryStorage()


async def on_startup(bot: Bot) -> None:
    session_maker: async_sessionmaker[AsyncSession] = get_session_maker()
    async with session_maker() as session:
        await seed_initial_categories(session)


async def on_shutdown(bot: Bot) -> None:
    engine: AsyncEngine = get_async_engine()
    await engine.dispose()


async def main() -> None:
    settings: Settings = get_settings()
    session_maker: async_sessionmaker[AsyncSession] = get_session_maker()
    storage: BaseStorage = await create_fsm_storage(settings.redis_url)

    bot: Bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.MARKDOWN,
        ),
    )
    dp: Dispatcher = Dispatcher(storage=storage)

    dp.update.outer_middleware(
        DbSessionMiddleware(session_maker=session_maker),
    )
    dp.update.outer_middleware(ServicesMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    dp.update.outer_middleware(UserI18nMiddleware())

    dp.include_router(main_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    asyncio.run(main())


if __name__ == "__main__":
    run()
