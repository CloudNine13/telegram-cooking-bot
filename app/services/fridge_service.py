import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.fridge import FridgeItem
from app.database.repositories.fridge_repo import FridgeRepo
from app.schemas.fridge import FridgeItemDTO


class FridgeService:
    def __init__(
        self,
        fridge_repo: FridgeRepo | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        if fridge_repo is not None:
            self.fridge_repo: FridgeRepo = fridge_repo
        elif session is not None:
            self.fridge_repo = FridgeRepo(session)
        else:
            raise ValueError("Either fridge_repo or session must be provided")

        self.session: AsyncSession = self.fridge_repo.session

    @staticmethod
    def normalize_ingredient(name: str) -> str:
        lowered: str = name.lower().strip()
        cleaned: str = re.sub(r"[^\w\s]", " ", lowered)
        normalized: str = re.sub(r"\s+", " ", cleaned).strip()

        return normalized

    @classmethod
    def parse_raw_ingredients(cls, text: str) -> list[tuple[str, str]]:
        tokens: list[str] = re.split(r"[,;\n]+", text)
        result: list[tuple[str, str]] = []
        seen_normalized: set[str] = set()

        for token in tokens:
            raw_name: str = token.strip()
            if not raw_name:
                continue

            norm_name: str = cls.normalize_ingredient(raw_name)
            if not norm_name or norm_name in seen_normalized:
                continue

            seen_normalized.add(norm_name)
            result.append((raw_name, norm_name))

        return result

    async def get_user_items(self, user_id: int) -> list[FridgeItemDTO]:
        items: list[FridgeItem] = await self.fridge_repo.get_user_items(user_id)

        return [FridgeItemDTO.model_validate(item) for item in items]

    async def get_user_normalized_names(self, user_id: int) -> list[str]:
        return await self.fridge_repo.get_user_normalized_names(user_id)

    async def add_ingredients(
        self,
        user_id: int,
        raw_text: str,
    ) -> list[FridgeItemDTO]:
        parsed_items = self.parse_raw_ingredients(raw_text)
        if not parsed_items:
            return []

        created_items: list[FridgeItem] = await self.fridge_repo.add_items(
            user_id=user_id,
            items=parsed_items,
        )
        await self.session.commit()

        return [FridgeItemDTO.model_validate(item) for item in created_items]

    async def replace_ingredients(
        self,
        user_id: int,
        raw_text: str,
    ) -> list[FridgeItemDTO]:
        parsed_items = self.parse_raw_ingredients(raw_text)
        created_items: list[FridgeItem] = await self.fridge_repo.replace_items(
            user_id=user_id,
            items=parsed_items,
        )
        await self.session.commit()

        return [FridgeItemDTO.model_validate(item) for item in created_items]

    async def clear_fridge(self, user_id: int) -> int:
        count: int = await self.fridge_repo.clear_items(user_id)
        await self.session.commit()

        return count

    async def delete_item(self, user_id: int, item_id: int) -> bool:
        result: bool = await self.fridge_repo.delete_item(user_id, item_id)
        if result:
            await self.session.commit()

        return result

    async def delete_item_by_name(self, user_id: int, raw_name: str) -> bool:
        normalized_name: str = self.normalize_ingredient(raw_name)
        result: bool = await self.fridge_repo.delete_item_by_name(
            user_id,
            normalized_name,
        )
        if result:
            await self.session.commit()

        return result
