"""Mini UMS API app factory.

M1: liveness and readiness only. Schema, seed data, auth and the student data API arrive in M2.
Run with `uvicorn mini_ums_api.main:create_app --factory`.
"""

from collections.abc import Mapping
from importlib.metadata import version

from fastapi import FastAPI

from mini_ums_api.settings import Settings
from voiceserve_common.health import Check, health_router, postgres_check
from voiceserve_common.logs import configure_logging

__version__ = version("mini-ums-api")


def default_checks(settings: Settings) -> dict[str, Check]:
    return {"postgres": postgres_check(settings.database_url, require_extensions=("vector",))}


def create_app(
    settings: Settings | None = None, checks: Mapping[str, Check] | None = None
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.service_name, settings.log_level)
    app = FastAPI(title="Mini UMS API", version=__version__)
    app.include_router(
        health_router(
            settings.service_name,
            __version__,
            default_checks(settings) if checks is None else checks,
        )
    )
    return app
