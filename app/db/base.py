from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    This module should only contain the base class; actual models live in
    ``app.models``. Keeping models out of this file avoids circular imports
    (the old version imported ``Base`` from itself) and keeps responsibilities
    separated.
    """

    pass
