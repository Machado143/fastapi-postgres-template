from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.logging import user_id_ctx_var
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        user_id = int(decode_access_token(token))
    except (ValueError, TypeError):
        raise UnauthorizedException()
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException()
    if not user.is_active:
        raise UnauthorizedException("Inactive user")
    # inject user_id into logging context for the remainder of this request
    user_id_ctx_var.set(user.id)
    return user
