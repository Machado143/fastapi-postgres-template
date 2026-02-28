import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService
from app.models.user import User
from tests.conftest import TEST_PASSWORD


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    data = UserCreate(
        email="svc_test@example.com",
        password=TEST_PASSWORD,
        full_name="Test User",
    )
    user = await service.create_user(data)
    assert user.id is not None
    assert user.email == "svc_test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_create_user_duplicate_email(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    data = UserCreate(email="dup_svc@example.com", password=TEST_PASSWORD)
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
        UserCreate(email="update_svc@example.com", password=TEST_PASSWORD)
    )
    updated = await service.update_user(
        created.id, UserUpdate(full_name="Updated Name")
    )
    assert updated.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    created = await service.create_user(
        UserCreate(email="delete_svc@example.com", password=TEST_PASSWORD)
    )
    await service.delete_user(created.id)
    with pytest.raises(NotFoundException):
        await service.get_user(created.id)


@pytest.mark.asyncio
async def test_list_users(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    await service.create_user(
        UserCreate(email="list1_svc@example.com", password=TEST_PASSWORD)
    )
    await service.create_user(
        UserCreate(email="list2_svc@example.com", password=TEST_PASSWORD)
    )
    page = await service.list_users(limit=100, offset=0)
    assert page.total >= 2
    assert len(page.items) >= 2


@pytest.mark.asyncio
async def test_create_user_race_condition(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    data = UserCreate(email="race@example.com", password=TEST_PASSWORD)
    # first create succeeds
    await service.create_user(data)

    # simulate race by bypassing the email check in service
    async def no_check(email: str):
        return None

    service.repo.get_by_email = no_check  # type: ignore

    with pytest.raises(ConflictException):
        await service.create_user(data)

    # verify that only one record exists in the database
    result = await db_session.execute(
        select(func.count()).select_from(User).where(User.email == data.email)
    )
    assert result.scalar_one() == 1
