import asyncio

import httpx
from fastapi import FastAPI

from voiceserve_common.health import Check, health_router


async def _ok() -> str:
    return "fine"


async def _fails() -> str:
    raise ConnectionError("refused by 10.0.0.5 for student 12215678")


async def _hangs() -> str:
    await asyncio.sleep(10)
    return "never"


def _client(checks: dict[str, Check]) -> httpx.AsyncClient:
    app = FastAPI()
    app.include_router(health_router("svc", "0.1.0", checks, timeout_s=0.2))
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_health_is_always_ok() -> None:
    async with _client({"db": _fails}) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "svc", "version": "0.1.0"}


async def test_ready_when_all_checks_pass() -> None:
    async with _client({"a": _ok, "b": _ok}) as client:
        response = await client.get("/ready")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ready"
    assert body["checks"]["a"]["ok"] is True
    assert body["checks"]["a"]["detail"] == "fine"


async def test_ready_with_no_checks() -> None:
    async with _client({}) as client:
        response = await client.get("/ready")
    assert response.status_code == 200


async def test_not_ready_when_a_check_raises() -> None:
    async with _client({"a": _ok, "db": _fails}) as client:
        response = await client.get("/ready")
    body = response.json()
    assert response.status_code == 503
    assert body["status"] == "not_ready"
    assert body["checks"]["a"]["ok"] is True
    assert body["checks"]["db"]["ok"] is False
    assert body["checks"]["db"]["error"].startswith("ConnectionError")
    assert "12215678" not in body["checks"]["db"]["error"]


async def test_not_ready_when_a_check_times_out() -> None:
    async with _client({"slow": _hangs}) as client:
        response = await client.get("/ready")
    assert response.status_code == 503
    assert "timed out" in response.json()["checks"]["slow"]["error"]
