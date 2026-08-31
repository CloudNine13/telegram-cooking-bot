import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.fridge import FridgeItem
from app.database.repositories.fridge_repo import FridgeRepo
from app.schemas.fridge import FridgeItemCreateDTO, FridgeItemDTO


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
    def parse_raw_ingredients(cls, text: str) -> list[FridgeItemCreateDTO]:
        tokens: list[str] = re.split(r"[,;\n]+", text)
        result: list[FridgeItemCreateDTO] = []
        seen_normalized: set[str] = set()

        for token in tokens:
            raw_name: str = token.strip()
            if not raw_name:
                continue

            norm_name: str = cls.normalize_ingredient(raw_name)
            if not norm_name or norm_name in seen_normalized:
                continue

            seen_normalized.add(norm_name)
            result.append(
                FridgeItemCreateDTO(
                    raw_name=raw_name,
                    normalized_name=norm_name,
                ),
            )

        return result

    async def get_shared_items(self) -> list[FridgeItemDTO]:
        items: list[FridgeItem] = await self.fridge_repo.get_all()

        return [FridgeItemDTO.model_validate(item) for item in items]

    async def add_ingredients(self, raw_text: str) -> list[FridgeItemDTO]:
        dtos: list[FridgeItemCreateDTO] = self.parse_raw_ingredients(raw_text)
        if not dtos:
            return []

        created: list[FridgeItem] = await self.fridge_repo.bulk_create(dtos)
        await self.session.commit()

        return [FridgeItemDTO.model_validate(item) for item in created]

    async def remove_item(self, item_id: int) -> bool:
        result: bool = await self.fridge_repo.delete_by_id(item_id)
        if result:
            await self.session.commit()

        return result

    async def replace_ingredients(self, raw_text: str) -> list[FridgeItemDTO]:
        dtos: list[FridgeItemCreateDTO] = self.parse_raw_ingredients(raw_text)
        created: list[FridgeItem] = await self.fridge_repo.replace_all(dtos)
        await self.session.commit()

        return [FridgeItemDTO.model_validate(item) for item in created]

    async def clear_fridge(self) -> int:
        count: int = await self.fridge_repo.delete_all()
        await self.session.commit()

        return count
