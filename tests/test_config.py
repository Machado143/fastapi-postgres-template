from app.core.config import Settings
from tests.conftest import TEST_PG_DATABASE_URL, TEST_SECRET_KEY


def test_asyncpg_prefix():
    # if DATABASE_URL comes without +asyncpg, validator adds it.
    # _env_file=None prevents pydantic-settings from loading the local .env,
    # ensuring the values passed as kwargs are the ones actually used.
    s = Settings(
        _env_file=None,
        DATABASE_URL=TEST_PG_DATABASE_URL,
        SECRET_KEY=TEST_SECRET_KEY,
    )
    assert str(s.DATABASE_URL).startswith("postgresql+asyncpg://")


def test_debug_disabled_in_production():
    s = Settings(
        _env_file=None,
        DATABASE_URL=TEST_PG_DATABASE_URL,
        SECRET_KEY=TEST_SECRET_KEY,
        ENV="production",
        DEBUG=True,  # should be forced to False in production
    )
    assert s.DEBUG is False
