"""Fixtures for API tests against a real Postgres.

A throwaway `voiceserve_test` database is created once per test session on the server in
TEST_DATABASE_ADMIN_URL (default: the `make up` database on localhost:5433), migrated and
seeded with a small population plus the personas. Without a reachable server the API tests
are skipped, unless REQUIRE_DB=1 (set by CI and `make test`), in which case they fail.
"""

import asyncio
import os
from collections.abc import AsyncIterator, Awaitable, Callable

import asyncpg
import httpx
import pytest

from mini_ums_api.db import create_pool, migrate
from mini_ums_api.main import create_app
from mini_ums_api.seed.load import seed_database
from mini_ums_api.seed.personas import PERSONA_PASSWORD
from mini_ums_api.settings import Settings

ADMIN_URL = os.environ.get(
    "TEST_DATABASE_ADMIN_URL", "postgresql://voiceserve:voiceserve@localhost:5433/voiceserve"
)
TEST_DB = "voiceserve_test"


def _with_database(url: str, name: str) -> str:
    return url.rsplit("/", 1)[0] + "/" + name


async def _prepare(url: str) -> None:
    admin = await asyncpg.connect(ADMIN_URL, timeout=5)
    try:
        await admin.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
        await admin.execute(f"CREATE DATABASE {TEST_DB}")
    finally:
        await admin.close()
    pool = await create_pool(url)
    try:
        await pool.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await migrate(pool)
        await seed_database(pool, seed=7, today=None, n_students=40)
    finally:
        await pool.close()


async def _reachable() -> str | None:
    try:
        conn = await asyncpg.connect(ADMIN_URL, timeout=3)
    except (OSError, asyncpg.PostgresError) as exc:
        return f"{type(exc).__name__}: {exc}"
    await conn.close()
    return None


@pytest.fixture(scope="session")
def database_url() -> str:
    problem = asyncio.run(_reachable())
    if problem is not None:
        if os.environ.get("REQUIRE_DB") == "1":
            pytest.fail(f"Postgres required but unreachable at {ADMIN_URL}: {problem}")
        pytest.skip(f"Postgres not reachable ({problem}); run `make up` first")
    url = _with_database(ADMIN_URL, TEST_DB)
    asyncio.run(_prepare(url))
    return url


@pytest.fixture
async def client(database_url: str) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(database_url=database_url, seed_on_empty=False, environment="dev")
    app = create_app(settings, checks={})
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c,
    ):
        yield c


Login = Callable[[str], Awaitable[dict[str, str]]]


@pytest.fixture
def login(client: httpx.AsyncClient) -> Login:
    async def _login(reg_no: str) -> dict[str, str]:
        response = await client.post(
            "/auth/login", json={"reg_no": reg_no, "password": PERSONA_PASSWORD}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['token']}"}

    return _login
