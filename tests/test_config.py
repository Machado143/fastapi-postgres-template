from app.core.config import Settings


def test_asyncpg_prefix():
    # if DATABASE_URL comes without +asyncpg, validator adds it
    s = Settings(
        DATABASE_URL="postgresql://user:pass@localhost/db",
        JWT_SECRET_KEY="secret",
    )
    assert str(s.DATABASE_URL).startswith("postgresql+asyncpg://")


def test_debug_disabled_in_production():
    s = Settings(
        DATABASE_URL="postgresql://user:pass@localhost/db",
        JWT_SECRET_KEY="secret",
        ENV="production",
        DEBUG=True,  # should be ignored
    )
    assert s.DEBUG is False
