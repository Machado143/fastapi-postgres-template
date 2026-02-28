from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, token: RefreshToken) -> RefreshToken:
        self.session.add(token)
        await self.session.flush()
        await self.session.refresh(token)
        return token

    async def get_by_token(self, token_str: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token == token_str)
        )
        return result.scalar_one_or_none()

    async def delete(self, token: RefreshToken) -> None:
        await self.session.delete(token)
        await self.session.flush()
