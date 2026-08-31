from sqlalchemy.ext.asyncio import AsyncSession

from app.services.category_service import CategoryService


async def seed_initial_categories(session: AsyncSession) -> None:
    category_service: CategoryService = CategoryService(session=session)
    await category_service.seed_default_categories()
