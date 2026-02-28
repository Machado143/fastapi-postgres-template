from sqladmin import ModelView

from app.models.refresh_token import RefreshToken
from app.models.user import User


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"

    # Columns shown in the list view
    column_list = [
        User.id,
        User.email,
        User.full_name,
        User.is_active,
        User.is_superuser,
        User.created_at,
    ]

    # Columns available for search
    column_searchable_list = [User.email, User.full_name]

    # Columns available for filtering
    column_filters = [User.is_active, User.is_superuser, User.created_at]

    # Columns sortable in the list view
    column_sortable_list = [User.id, User.email, User.created_at]

    # Fields excluded from create/edit forms — never expose hashed_password
    form_excluded_columns = [User.hashed_password, User.refresh_tokens]

    # Mark sensitive columns as not exportable
    can_export = False

    # Default ordering
    column_default_sort = [(User.id, True)]  # descending


class RefreshTokenAdmin(ModelView, model=RefreshToken):
    name = "Refresh Token"
    name_plural = "Refresh Tokens"
    icon = "fa-solid fa-key"

    # token value is intentionally omitted — must never be visible in admin
    column_list = [
        RefreshToken.id,
        RefreshToken.user_id,
        RefreshToken.expires_at,
        RefreshToken.revoked,
        RefreshToken.created_at,
    ]

    column_filters = [RefreshToken.revoked, RefreshToken.expires_at]
    column_sortable_list = [RefreshToken.id, RefreshToken.expires_at]

    # token must also be excluded from detail and form views
    form_excluded_columns = [RefreshToken.token]

    can_create = False   # tokens are only created via auth flow
    can_export = False
    can_delete = True    # allow manual revocation
