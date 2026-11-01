import httpx
import pytest

from gateway.main import create_app, default_checks
from gateway.settings import Settings

UNREACHABLE = Settings(orchestrator_url="http://127.0.0.1:1", livekit_url="ws://127.0.0.1:1")


def _client(settings: Settings) -> httpx.AsyncClient:
    app = create_app(settings)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_health() -> None:
    async with _client(UNREACHABLE) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "gateway"


def test_readiness_checks_orchestrator_and_livekit() -> None:
    assert set(default_checks(UNREACHABLE)) == {"orchestrator", "livekit"}


@pytest.mark.parametrize(
    ("livekit_url", "http_url"),
    [
        ("ws://livekit:7880", "http://livekit:7880"),
        ("wss://x.livekit.cloud", "https://x.livekit.cloud"),
    ],
)
def test_livekit_http_url(livekit_url: str, http_url: str) -> None:
    assert Settings(livekit_url=livekit_url).livekit_http_url == http_url


async def test_not_ready_without_dependencies() -> None:
    async with _client(UNREACHABLE) as client:
        response = await client.get("/ready")
    checks = response.json()["checks"]
    assert response.status_code == 503
    assert checks["orchestrator"]["ok"] is False
    assert checks["livekit"]["ok"] is False
