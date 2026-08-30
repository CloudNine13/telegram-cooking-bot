from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database.models.fridge import FridgeItem
from app.database.repositories.base import BaseRepo
from app.schemas.fridge import FridgeItemCreateDTO


class FridgeRepo(BaseRepo):
    async def get_all(self) -> list[FridgeItem]:
        stmt = select(FridgeItem).order_by(
            FridgeItem.raw_name.asc(),
            FridgeItem.id.asc(),
        )
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def get_by_id(self, item_id: int) -> FridgeItem | None:
        stmt = select(FridgeItem).where(FridgeItem.id == item_id)
        result = await self.session.scalars(stmt)

        return result.first()

    async def get_normalized_names(self) -> list[str]:
        stmt = select(FridgeItem.normalized_name).order_by(FridgeItem.id.asc())
        result = await self.session.scalars(stmt)

        return list(result.all())

    async def bulk_create(
        self,
        items: list[FridgeItemCreateDTO],
    ) -> list[FridgeItem]:
        if not items:
            return []

        values_list: list[dict[str, str]] = [
            {
                "raw_name": item.raw_name,
                "normalized_name": item.normalized_name or item.raw_name,
            }
            for item in items
            if (item.normalized_name or item.raw_name)
        ]
        if not values_list:
            return []

        stmt = (
            pg_insert(FridgeItem)
            .values(values_list)
            .on_conflict_do_nothing(index_elements=["normalized_name"])
            .returning(FridgeItem)
        )
        result = await self.session.scalars(stmt)
        inserted: list[FridgeItem] = list(result.all())
        await self.session.flush()

        return inserted

    async def delete_by_id(self, item_id: int) -> bool:
        stmt = delete(FridgeItem).where(FridgeItem.id == item_id)
        result = await self.session.execute(stmt)

        return result.rowcount > 0

    async def delete_all(self) -> int:
        stmt = delete(FridgeItem)
        result = await self.session.execute(stmt)

        return result.rowcount

    async def replace_all(
        self,
        items: list[FridgeItemCreateDTO],
    ) -> list[FridgeItem]:
        await self.delete_all()

        return await self.bulk_create(items)
