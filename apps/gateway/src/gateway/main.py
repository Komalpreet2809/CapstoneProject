"""Gateway app factory.

M1: liveness and readiness only. The LiveKit agent worker, VAD and barge-in arrive in M3.
Run with `uvicorn gateway.main:create_app --factory`.
"""

from collections.abc import Mapping
from importlib.metadata import version

from fastapi import FastAPI

from gateway.settings import Settings
from voiceserve_common.health import Check, health_router, http_check
from voiceserve_common.logs import configure_logging

__version__ = version("gateway")


def default_checks(settings: Settings) -> dict[str, Check]:
    return {
        "orchestrator": http_check(f"{settings.orchestrator_url}/health"),
        "livekit": http_check(settings.livekit_http_url),
    }


def create_app(
    settings: Settings | None = None, checks: Mapping[str, Check] | None = None
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.service_name, settings.log_level)
    app = FastAPI(title="VoiceServe Gateway", version=__version__)
    app.include_router(
        health_router(
            settings.service_name,
            __version__,
            default_checks(settings) if checks is None else checks,
        )
    )
    return app
