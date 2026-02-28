from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core.config import settings


class AdminAuth(AuthenticationBackend):
    """
    Simple token-based authentication for the sqladmin panel.

    In production replace this with a proper check against the DB
    (superuser flag) or a dedicated admin credential env var.
    The token is the SECRET_KEY itself — rotate it to invalidate sessions.
    """

    async def login(self, request: Request) -> bool:
        form = await request.form()
        token = form.get("token", "")
        if token == settings.ADMIN_TOKEN:
            request.session["admin_token"] = token
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool | RedirectResponse:
        token = request.session.get("admin_token")
        if token != settings.ADMIN_TOKEN:
            return RedirectResponse(
                request.url_for("admin:login"), status_code=302
            )
        return True
