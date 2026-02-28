from fastapi import APIRouter, Depends, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserPage, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation error (e.g. password too short)"},
    },
)
async def create_user(
    data: UserCreate = Body(...),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Register a new user. Email must be unique. Password: 8–72 bytes."""
    service = UserService(db)
    return await service.create_user(data)


@router.get(
    "",
    response_model=UserPage,
    summary="List users (paginated)",
    responses={401: {"description": "Missing or invalid token"}},
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number, 1-indexed"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> UserPage:
    """Returns a paginated list of users. Requires authentication."""
    service = UserService(db)
    offset = (page - 1) * limit
    return await service.list_users(limit=limit, offset=offset)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current authenticated user",
    responses={401: {"description": "Missing or invalid token"}},
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """Returns the profile of the currently authenticated user."""
    return UserRead.model_validate(current_user)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user by ID",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "User not found"},
    },
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> UserRead:
    """Fetch a single user by their numeric ID."""
    service = UserService(db)
    return await service.get_user(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Partially update a user",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "User not found"},
        409: {"description": "Email already taken"},
    },
)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> UserRead:
    """Update one or more fields of an existing user. All fields optional."""
    service = UserService(db)
    return await service.update_user(user_id, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> None:
    """Permanently delete a user and all their refresh tokens."""
    service = UserService(db)
    await service.delete_user(user_id)
