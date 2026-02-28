import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    data = UserCreate(email="svc_test@example.com", password="secret123", full_name="Test User")
    user = await service.create_user(data)
    assert user.id is not None
    assert user.email == "svc_test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_create_user_duplicate_email(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    data = UserCreate(email="dup_svc@example.com", password="secret123")
    await service.create_user(data)
    with pytest.raises(ConflictException):
        await service.create_user(data)


@pytest.mark.asyncio
async def test_get_user_not_found(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    with pytest.raises(NotFoundException):
        await service.get_user(99999)


@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    created = await service.create_user(
        UserCreate(email="update_svc@example.com", password="secret123")
    )
    updated = await service.update_user(created.id, UserUpdate(full_name="Updated Name"))
    assert updated.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    created = await service.create_user(
        UserCreate(email="delete_svc@example.com", password="secret123")
    )
    await service.delete_user(created.id)
    with pytest.raises(NotFoundException):
        await service.get_user(created.id)


@pytest.mark.asyncio
async def test_list_users(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    await service.create_user(UserCreate(email="list1_svc@example.com", password="secret123"))
    await service.create_user(UserCreate(email="list2_svc@example.com", password="secret123"))
    page = await service.list_users(limit=100, offset=0)
    assert page.total >= 2
    assert len(page.items) >= 2
