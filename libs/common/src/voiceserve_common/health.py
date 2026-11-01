"""`/health` (liveness) and `/ready` (dependency checks) for every Python service.

A check is an async callable that returns a short detail string on success and raises on
failure. `/ready` runs all checks concurrently with a timeout and answers 503 if any fail,
which is what the Compose healthchecks poll.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

import asyncpg
import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from voiceserve_common.masking import mask_text

Check = Callable[[], Awaitable[str]]


async def _run_check(check: Check, timeout_s: float) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        detail = await asyncio.wait_for(check(), timeout=timeout_s)
        result: dict[str, Any] = {"ok": True, "detail": detail}
    except TimeoutError:
        result = {"ok": False, "error": f"timed out after {timeout_s}s"}
    except Exception as exc:
        result = {"ok": False, "error": mask_text(f"{type(exc).__name__}: {exc}")}
    result["ms"] = round((time.perf_counter() - started) * 1000, 1)
    return result


def health_router(
    service: str,
    version: str,
    checks: Mapping[str, Check],
    timeout_s: float = 2.0,
) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": service, "version": version}

    @router.get("/ready")
    async def ready() -> JSONResponse:
        names = list(checks)
        results = await asyncio.gather(*(_run_check(checks[n], timeout_s) for n in names))
        by_name = dict(zip(names, results, strict=True))
        ok = all(r["ok"] for r in results)
        return JSONResponse(
            status_code=200 if ok else 503,
            content={
                "status": "ready" if ok else "not_ready",
                "service": service,
                "checks": by_name,
            },
        )

    return router


def postgres_check(dsn: str, require_extensions: tuple[str, ...] = ()) -> Check:
    async def check() -> str:
        conn = await asyncpg.connect(dsn)
        try:
            rows = await conn.fetch("SELECT extname, extversion FROM pg_extension")
        finally:
            await conn.close()
        installed = {r["extname"]: r["extversion"] for r in rows}
        missing = [e for e in require_extensions if e not in installed]
        if missing:
            raise RuntimeError(f"missing extensions: {', '.join(missing)}")
        return ", ".join(f"{e} {installed[e]}" for e in require_extensions) or "connected"

    return check


def redis_check(url: str) -> Check:
    async def check() -> str:
        client = aioredis.from_url(url)
        try:
            await client.ping()
        finally:
            await client.aclose()
        return "PONG"

    return check


def http_check(url: str) -> Check:
    async def check() -> str:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
        response.raise_for_status()
        return f"HTTP {response.status_code}"

    return check
