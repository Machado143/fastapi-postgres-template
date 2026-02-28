from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.token import Token, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.core.limiter import limiter

router = APIRouter()


@router.post("/token", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Login endpoint — rate limited to 10 attempts per minute per IP."""
    service = AuthService(db)
    return await service.authenticate(form_data.username, form_data.password)


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Token refresh — rate limited to 20 per minute per IP."""
    service = AuthService(db)
    return await service.refresh(payload.refresh_token)
