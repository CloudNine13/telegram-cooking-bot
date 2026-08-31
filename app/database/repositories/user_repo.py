from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.database.models.user import User
from app.database.repositories.base import BaseRepo
from app.schemas.user import UserCreateOrUpdateDTO


class UserRepo(BaseRepo):
    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.scalars(stmt)

        return result.one_or_none()

    async def upsert(self, dto: UserCreateOrUpdateDTO) -> User:
        stmt = (
            insert(User)
            .values(
                id=dto.id,
                username=dto.username,
                full_name=dto.full_name,
                language_code=dto.language_code,
            )
            .on_conflict_do_update(
                index_elements=[User.id],
                set_={
                    "username": dto.username,
                    "full_name": dto.full_name,
                },
            )
            .returning(User)
        )
        result = await self.session.scalars(stmt)
        user: User = result.one()
        await self.session.commit()

        return user

    async def update_language(
        self,
        user_id: int,
        language_code: str,
    ) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(language_code=language_code)
            .returning(User)
        )
        result = await self.session.scalars(stmt)
        user: User | None = result.one_or_none()
        if user is not None:
            await self.session.commit()

        return user

    async def get_all(self) -> list[User]:
        stmt = select(User).order_by(User.id.asc())
        result = await self.session.scalars(stmt)

        return list(result.all())
