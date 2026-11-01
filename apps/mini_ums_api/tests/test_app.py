import httpx

from mini_ums_api.main import create_app, default_checks
from mini_ums_api.settings import Settings

UNREACHABLE = Settings(database_url="postgresql://u:p@127.0.0.1:1/none")


def _client(settings: Settings) -> httpx.AsyncClient:
    app = create_app(settings)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_health() -> None:
    async with _client(UNREACHABLE) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "mini_ums_api"


def test_readiness_checks_postgres() -> None:
    assert set(default_checks(UNREACHABLE)) == {"postgres"}


async def test_not_ready_without_database() -> None:
    async with _client(UNREACHABLE) as client:
        response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["postgres"]["ok"] is False
