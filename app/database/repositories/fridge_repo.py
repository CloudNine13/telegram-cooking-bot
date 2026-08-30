from sqlalchemy import delete, select

from app.database.models.fridge import FridgeItem
from app.database.repositories.base import BaseRepo


class FridgeRepo(BaseRepo):
    async def get_user_items(self, user_id: int) -> list[FridgeItem]:
        stmt = (
            select(FridgeItem)
            .where(FridgeItem.user_id == user_id)
            .order_by(FridgeItem.created_at.asc(), FridgeItem.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def get_user_normalized_names(self, user_id: int) -> list[str]:
        stmt = (
            select(FridgeItem.normalized_name)
            .where(FridgeItem.user_id == user_id)
            .order_by(FridgeItem.id.asc())
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def add_items(
        self,
        user_id: int,
        items: list[tuple[str, str]],
    ) -> list[FridgeItem]:
        created_items: list[FridgeItem] = []
        for raw_name, normalized_name in items:
            item = FridgeItem(
                user_id=user_id,
                raw_name=raw_name,
                normalized_name=normalized_name,
            )
            self.session.add(item)
            created_items.append(item)

        await self.session.flush()

        return created_items

    async def replace_items(
        self,
        user_id: int,
        items: list[tuple[str, str]],
    ) -> list[FridgeItem]:
        await self.clear_items(user_id)

        return await self.add_items(user_id, items)

    async def clear_items(self, user_id: int) -> int:
        stmt = delete(FridgeItem).where(FridgeItem.user_id == user_id)
        result = await self.session.execute(stmt)

        return result.rowcount

    async def delete_item(self, user_id: int, item_id: int) -> bool:
        stmt = delete(FridgeItem).where(
            FridgeItem.user_id == user_id,
            FridgeItem.id == item_id,
        )
        result = await self.session.execute(stmt)

        return result.rowcount > 0

    async def delete_item_by_name(
        self,
        user_id: int,
        normalized_name: str,
    ) -> bool:
        stmt = delete(FridgeItem).where(
            FridgeItem.user_id == user_id,
            FridgeItem.normalized_name == normalized_name,
        )
        result = await self.session.execute(stmt)

        return result.rowcount > 0
