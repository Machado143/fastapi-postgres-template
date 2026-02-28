from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, verify_password
from app.models.refresh_token import RefreshToken
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.token import Token


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)

    async def authenticate(self, email: str, password: str) -> Token:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedException("Inactive user")
        access_token = create_access_token(subject=user.id)
        refresh = await self._create_refresh_token(user)
        return Token(access_token=access_token, refresh_token=refresh.token)

    async def _create_refresh_token(self, user) -> RefreshToken:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        rt = RefreshToken(user_id=user.id, token=token, expires_at=expires)
        async with self.session.begin():
            rt = await self.refresh_repo.create(rt)
        return rt

    async def refresh(self, refresh_token: str) -> Token:
        rt = await self.refresh_repo.get_by_token(refresh_token)
        if not rt or rt.expires_at < datetime.now(timezone.utc) or rt.revoked:
            raise UnauthorizedException("Invalid refresh token")
        user = await self.repo.get_by_id(rt.user_id)
        if not user:
            raise UnauthorizedException("Invalid refresh token")
        async with self.session.begin():
            await self.refresh_repo.delete(rt)
            new_rt = await self._create_refresh_token(user)
        access = create_access_token(subject=user.id)
        return Token(access_token=access, refresh_token=new_rt.token)
