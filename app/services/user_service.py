from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserPage, UserRead, UserUpdate

_EMAIL_CONFLICT = "Email already registered"


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    async def create_user(self, data: UserCreate) -> UserRead:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ConflictException(_EMAIL_CONFLICT)
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        try:
            async with self.session.begin_nested():
                user = await self.repo.create(user)
        except IntegrityError:
            raise ConflictException(_EMAIL_CONFLICT)
        return UserRead.model_validate(user)

    async def get_user(self, user_id: int) -> UserRead:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        return UserRead.model_validate(user)

    async def list_users(self, limit: int = 20, offset: int = 0) -> UserPage:
        users, total = await self.repo.list(limit=limit, offset=offset)
        return UserPage(
            items=[UserRead.model_validate(u) for u in users],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_user(self, user_id: int, data: UserUpdate) -> UserRead:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        if data.email is not None and data.email != user.email:
            conflict = await self.repo.get_by_email(data.email)
            if conflict:
                raise ConflictException(_EMAIL_CONFLICT)
            user.email = data.email
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.password is not None:
            user.hashed_password = hash_password(data.password)
        if data.is_active is not None:
            user.is_active = data.is_active
        try:
            async with self.session.begin_nested():
                user = await self.repo.update(user)
        except IntegrityError:
            raise ConflictException(_EMAIL_CONFLICT)
        return UserRead.model_validate(user)

    async def delete_user(self, user_id: int) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        async with self.session.begin_nested():
            await self.repo.delete(user)
