from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Environment must be configured before importing application settings.
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT / ".env.test", override=True)


def _integer_env(name: str, default: int) -> None:
    value = os.getenv(name, "")
    os.environ[name] = value if value.isdigit() else str(default)


base_database = os.getenv("TEST_DB_NAME") or os.getenv("DB_NAME", "")
if not base_database:
    raise RuntimeError("DB_NAME is required before tests can start")

test_database = base_database
if not test_database.endswith("_test"):
    test_database = f"{test_database}_test"

os.environ["DB_NAME"] = test_database
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "true"
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-change-me-0123456789")
os.environ["REDIS_HOST"] = os.getenv("TEST_REDIS_HOST", "127.0.0.1")
_integer_env("REDIS_PORT", 6379)
_integer_env("REDIS_DB", 1)
_integer_env("OUTBOX_BACKOFF_POLL_DELAY", 1)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def database() -> AsyncIterator[None]:
    from tortoise import Tortoise

    from settings import settings
    from tests.helpers.database import seed_roles

    await Tortoise.init(
        config=settings.TORTOISE_ORM,
        _enable_global_fallback=True,
        _create_db=True,
    )
    await Tortoise.generate_schemas(safe=True)
    await seed_roles()

    try:
        yield
    finally:
        await Tortoise.close_connections()


@pytest_asyncio.fixture(loop_scope="session")
async def seeded_roles(database: None):
    from tests.helpers.database import reset_database, seed_roles

    await reset_database()
    return await seed_roles()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def app(database: None):
    from src import create_app

    return create_app()


@pytest_asyncio.fixture(loop_scope="session")
async def client(app, seeded_roles) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as test_client:
        yield test_client


@pytest.fixture
def fake_redis(monkeypatch):
    from tests.helpers.redis import patch_redis_pool

    return patch_redis_pool(monkeypatch)


@pytest.fixture(scope="session")
def test_db_name() -> str:
    return os.environ["DB_NAME"]
