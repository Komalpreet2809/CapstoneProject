"""Gateway app factory: health, readiness and voice tokens.

The realtime half (VAD, STT, TTS, barge-in) is the LiveKit agent worker in `gateway.worker`,
run as its own process from the same image.
Run with `uvicorn gateway.main:create_app --factory`.
"""

from collections.abc import Mapping
from importlib.metadata import version

import redis.asyncio as aioredis
from fastapi import FastAPI

from gateway.settings import Settings
from gateway.tokens import router
from voiceserve_common.budget import BudgetGuard
from voiceserve_common.health import Check, health_router, http_check
from voiceserve_common.logs import configure_logging

__version__ = version("gateway")


def default_checks(settings: Settings) -> dict[str, Check]:
    return {
        "orchestrator": http_check(f"{settings.orchestrator_url}/health"),
        "livekit": http_check(settings.livekit_http_url),
    }


def create_app(
    settings: Settings | None = None,
    checks: Mapping[str, Check] | None = None,
    *,
    redis: aioredis.Redis | None = None,
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.service_name, settings.log_level)
    app = FastAPI(title="VoiceServe Gateway", version=__version__)
    app.state.settings = settings
    app.state.budget = BudgetGuard(
        redis or aioredis.from_url(settings.redis_url), settings.daily_budget_usd
    )
    app.include_router(
        health_router(
            settings.service_name,
            __version__,
            default_checks(settings) if checks is None else checks,
        )
    )
    app.include_router(router)
    return app
