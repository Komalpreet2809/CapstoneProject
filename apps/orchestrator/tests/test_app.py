import httpx

from orchestrator.main import create_app, default_checks
from orchestrator.settings import Settings

UNREACHABLE = Settings(redis_url="redis://127.0.0.1:1/0", mini_ums_api_url="http://127.0.0.1:1")


def _client(settings: Settings) -> httpx.AsyncClient:
    app = create_app(settings)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_health() -> None:
    async with _client(UNREACHABLE) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "orchestrator"


def test_readiness_checks_redis_and_mini_ums() -> None:
    assert set(default_checks(UNREACHABLE)) == {"redis", "mini_ums_api"}


async def test_not_ready_without_dependencies() -> None:
    async with _client(UNREACHABLE) as client:
        response = await client.get("/ready")
    checks = response.json()["checks"]
    assert response.status_code == 503
    assert checks["redis"]["ok"] is False
    assert checks["mini_ums_api"]["ok"] is False
