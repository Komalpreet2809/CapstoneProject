"""Orchestrator app factory.

M1: liveness and readiness only. The LangGraph agent arrives in M3 (one Ask feature) and M4.
Run with `uvicorn orchestrator.main:create_app --factory`.
"""

from collections.abc import Mapping
from importlib.metadata import version

from fastapi import FastAPI

from orchestrator.settings import Settings
from voiceserve_common.health import Check, health_router, http_check, redis_check
from voiceserve_common.logs import configure_logging

__version__ = version("orchestrator")


def default_checks(settings: Settings) -> dict[str, Check]:
    return {
        "redis": redis_check(settings.redis_url),
        "mini_ums_api": http_check(f"{settings.mini_ums_api_url}/health"),
    }


def create_app(
    settings: Settings | None = None, checks: Mapping[str, Check] | None = None
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.service_name, settings.log_level)
    app = FastAPI(title="VoiceServe Orchestrator", version=__version__)
    app.include_router(
        health_router(
            settings.service_name,
            __version__,
            default_checks(settings) if checks is None else checks,
        )
    )
    return app
