"""Orchestrator app factory: voice sessions, the agent graph and the streaming turn API.

Run with `uvicorn orchestrator.main:create_app --factory`.
"""

import logging
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from importlib.metadata import version

import anthropic
import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI

from orchestrator.api import router
from orchestrator.graph import build_graph
from orchestrator.intent import (
    Classifier,
    ClaudeClassifier,
    FallbackClassifier,
    ReplayClassifier,
    RulesClassifier,
)
from orchestrator.sessions import SessionStore
from orchestrator.settings import Settings
from orchestrator.ums import MiniUms
from voiceserve_common.budget import BudgetGuard
from voiceserve_common.health import Check, health_router, http_check, redis_check
from voiceserve_common.logs import configure_logging

__version__ = version("orchestrator")
log = logging.getLogger(__name__)


def default_checks(settings: Settings) -> dict[str, Check]:
    return {
        "redis": redis_check(settings.redis_url),
        "mini_ums_api": http_check(f"{settings.mini_ums_api_url}/health"),
    }


def make_classifier(settings: Settings, guard: BudgetGuard) -> Classifier:
    if settings.replay_mode:
        return ReplayClassifier.from_package()
    provider = settings.llm_provider or ("anthropic" if settings.anthropic_api_key else "rules")
    if provider == "rules":
        return RulesClassifier()
    client = anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key or None, timeout=8.0, max_retries=1
    )
    return FallbackClassifier(
        ClaudeClassifier(client, settings.llm_model, guard), RulesClassifier()
    )


def create_app(
    settings: Settings | None = None,
    checks: Mapping[str, Check] | None = None,
    *,
    redis: aioredis.Redis | None = None,
    ums_transport: httpx.AsyncBaseTransport | None = None,
    classifier: Classifier | None = None,
) -> FastAPI:
    """The keyword arguments let tests swap in fake Redis, a mock API and a fixed classifier."""
    settings = settings or Settings()
    configure_logging(settings.service_name, settings.log_level)
    redis = redis or aioredis.from_url(settings.redis_url)
    http = httpx.AsyncClient(
        base_url=settings.mini_ums_api_url, timeout=5.0, transport=ums_transport
    )
    guard = BudgetGuard(redis, settings.daily_budget_usd)
    classifier = classifier or make_classifier(settings, guard)
    ums = MiniUms(http)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("orchestrator ready", extra={"classifier": classifier.name})
        try:
            yield
        finally:
            await http.aclose()

    app = FastAPI(title="VoiceServe Orchestrator", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.redis = redis
    app.state.ums = ums
    app.state.sessions = SessionStore(redis, settings.session_ttl_seconds)
    app.state.graph = build_graph(classifier, ums)
    app.state.log = log
    app.include_router(
        health_router(
            settings.service_name,
            __version__,
            default_checks(settings) if checks is None else checks,
        )
    )
    app.include_router(router)
    return app
