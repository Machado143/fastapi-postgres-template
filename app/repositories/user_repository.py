import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[User], int]:
        # Run count and fetch concurrently — avoids sequential round-trips.
        count_q = self.session.execute(
            select(func.count()).select_from(User)
        )
        rows_q = self.session.execute(
            select(User)
            .order_by(User.id)
            .limit(limit)
            .offset(offset)
        )
        count_result, rows_result = await asyncio.gather(count_q, rows_q)
        return list(rows_result.scalars().all()), count_result.scalar_one()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()
