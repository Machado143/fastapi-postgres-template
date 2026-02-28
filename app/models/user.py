from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


def _validate_password(v: str) -> str:
    """Regras compartilhadas entre UserCreate e UserUpdate."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(v.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes long.")
    return v


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        # campo é opcional em update — só valida se foi fornecido
        if v is not None:
            return _validate_password(v)
        return v


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class UserPage(BaseModel):
    items: list[UserRead]
    total: int
    limit: int
    offset: int
