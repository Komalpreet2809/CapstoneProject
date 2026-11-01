import json

import httpx
import jwt
import pytest
from fakeredis import FakeAsyncRedis

from gateway.main import create_app
from gateway.settings import Settings
from voiceserve_common.budget import BudgetGuard

KEY = {"X-Internal-Key": "test-key"}
SESSION = {"session_id": "abcDEF123_-xyz789"}


def _client(settings: Settings, redis: FakeAsyncRedis | None = None) -> httpx.AsyncClient:
    app = create_app(settings, checks={}, redis=redis or FakeAsyncRedis())
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_internal_key_is_required() -> None:
    async with _client(Settings(internal_api_key="test-key")) as client:
        assert (await client.post("/voice-tokens", json=SESSION)).status_code == 403


async def test_no_voice_without_a_speech_provider() -> None:
    settings = Settings(internal_api_key="test-key", deepgram_api_key="", replay_mode=False)
    async with _client(settings) as client:
        body = (await client.post("/voice-tokens", json=SESSION, headers=KEY)).json()
    assert body == {"voice": None, "reason": "no_provider"}


async def test_replay_mode_offers_voice_and_dispatches_the_agent() -> None:
    settings = Settings(
        internal_api_key="test-key",
        replay_mode=True,
        livekit_public_url="ws://localhost:7880",
        livekit_api_secret="a-long-enough-test-secret-value",
    )
    async with _client(settings) as client:
        body = (await client.post("/voice-tokens", json=SESSION, headers=KEY)).json()
    voice = body["voice"]
    assert voice["mode"] == "replay" and voice["url"] == "ws://localhost:7880"
    claims = jwt.decode(voice["token"], "a-long-enough-test-secret-value", algorithms=["HS256"])
    assert claims["video"]["room"] == "vs-abcDEF123_-xyz789"
    assert claims["video"]["roomJoin"] is True
    dispatch = claims["roomConfig"]["agents"][0]
    assert dispatch["agentName"] == "voiceserve"
    assert json.loads(dispatch["metadata"]) == {"session_id": "abcDEF123_-xyz789"}
    assert claims["exp"] - claims["nbf"] <= 15 * 60


async def test_live_voice_stops_when_the_budget_is_spent() -> None:
    redis = FakeAsyncRedis()
    await BudgetGuard(redis, 1.0).record(0.995)
    settings = Settings(
        internal_api_key="test-key", deepgram_api_key="dg-test", daily_budget_usd=1.0
    )
    async with _client(settings, redis) as client:
        body = (await client.post("/voice-tokens", json=SESSION, headers=KEY)).json()
    assert body == {"voice": None, "reason": "budget"}


@pytest.mark.parametrize("session_id", ["short", "has spaces in it", "../../etc/passwd"])
async def test_session_ids_are_validated(session_id: str) -> None:
    settings = Settings(internal_api_key="test-key", replay_mode=True)
    async with _client(settings) as client:
        response = await client.post("/voice-tokens", json={"session_id": session_id}, headers=KEY)
    assert response.status_code == 422
