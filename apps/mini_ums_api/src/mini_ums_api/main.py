"""Mini UMS API app factory.

Run with `uvicorn mini_ums_api.main:create_app --factory`. On startup it applies pending
migrations and, when the database is empty and SEED_ON_EMPTY is set, generates synthetic data.
"""

import logging
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI

from mini_ums_api.db import create_pool, migrate
from mini_ums_api.routers import auth, hostel, public, rms, student
from mini_ums_api.seed.load import is_empty, seed_database
from mini_ums_api.settings import Settings
from voiceserve_common.health import Check, health_router, postgres_check
from voiceserve_common.logs import configure_logging

__version__ = version("mini-ums-api")
log = logging.getLogger(__name__)

DESCRIPTION = """
Synthetic university management system. **Demo data only.**

Personal routes live under `/me` and take the student from the session token
(`Authorization: Bearer <token>` from `POST /auth/login`), never from the request.
Writes require an `Idempotency-Key` header.
"""


def default_checks(settings: Settings) -> dict[str, Check]:
    return {"postgres": postgres_check(settings.database_url, require_extensions=("vector",))}


def create_app(
    settings: Settings | None = None, checks: Mapping[str, Check] | None = None
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.service_name, settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        pool = await create_pool(settings.database_url)
        applied = await migrate(pool)
        if applied:
            log.info("applied migrations", extra={"migrations": applied})
        if settings.seed_on_empty and await is_empty(pool):
            ds = await seed_database(
                pool, settings.seed, settings.seed_today, settings.seed_students
            )
            log.info(
                "seeded empty database",
                extra={"seed": settings.seed, "students": len(ds.rows("students"))},
            )
        app.state.pool = pool
        try:
            yield
        finally:
            await pool.close()

    app = FastAPI(
        title="Mini UMS API", version=__version__, description=DESCRIPTION, lifespan=lifespan
    )
    app.state.settings = settings
    app.include_router(
        health_router(
            settings.service_name,
            __version__,
            default_checks(settings) if checks is None else checks,
        )
    )
    for module in (auth, student, rms, hostel, public):
        app.include_router(module.router)
    return app
