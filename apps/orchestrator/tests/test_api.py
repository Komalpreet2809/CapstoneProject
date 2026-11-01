import json
from typing import Any

import httpx
import pytest
from fakeredis import FakeAsyncRedis

from orchestrator.intent import RulesClassifier
from orchestrator.main import create_app
from orchestrator.settings import Settings
from voiceserve_common import latency

GOOD_TOKEN = "token-of-a-logged-in-student"
KEY = {"X-Internal-Key": "test-key"}


@pytest.fixture
def redis() -> FakeAsyncRedis:
    return FakeAsyncRedis()


@pytest.fixture
def client(redis: FakeAsyncRedis, rows: list[dict[str, Any]]) -> httpx.AsyncClient:
    def mini_ums(request: httpx.Request) -> httpx.Response:
        if request.headers.get("Authorization") != f"Bearer {GOOD_TOKEN}":
            return httpx.Response(401, json={"detail": "Session expired"})
        if request.url.path == "/me":
            return httpx.Response(200, json={"reg_no": "24100001", "name": "Aarav Mehta"})
        if request.url.path == "/me/attendance":
            return httpx.Response(200, json=rows)
        return httpx.Response(404)

    app = create_app(
        Settings(internal_api_key="test-key"),
        checks={},
        redis=redis,
        ums_transport=httpx.MockTransport(mini_ums),
        classifier=RulesClassifier(),
    )
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def _session(client: httpx.AsyncClient) -> str:
    response = await client.post("/sessions", json={"api_token": GOOD_TOKEN}, headers=KEY)
    assert response.status_code == 201
    body = response.json()
    assert body["first_name"] == "Aarav"
    assert GOOD_TOKEN not in response.text  # the token never leaves the server side
    session_id: str = body["session_id"]
    return session_id


def _events(response: httpx.Response) -> list[dict[str, Any]]:
    return [json.loads(line) for line in response.text.splitlines() if line]


async def test_internal_key_is_required(client: httpx.AsyncClient) -> None:
    response = await client.post("/sessions", json={"api_token": GOOD_TOKEN})
    assert response.status_code == 403
    response = await client.post(
        "/sessions", json={"api_token": GOOD_TOKEN}, headers={"X-Internal-Key": "wrong"}
    )
    assert response.status_code == 403


async def test_an_invalid_portal_token_gets_no_session(client: httpx.AsyncClient) -> None:
    response = await client.post("/sessions", json={"api_token": "not-a-valid-token"}, headers=KEY)
    assert response.status_code == 401


async def test_a_turn_streams_sentences_then_card_then_done(
    client: httpx.AsyncClient, redis: FakeAsyncRedis
) -> None:
    session_id = await _session(client)
    response = await client.post(
        f"/sessions/{session_id}/turns",
        json={"text": "what's my attendance in computer networks?", "channel": "text"},
        headers=KEY,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    events = _events(response)
    kinds = [e["type"] for e in events]
    assert kinds == ["sentence"] * (len(kinds) - 2) + ["card", "done"]
    assert events[0]["text"].startswith("In CSE 326, Computer Networks")
    assert events[-2]["card"]["highlight"] == "CSE326"
    assert events[-1]["intent"] == "attendance"
    # text turns are recorded for `make latency`
    recorded = await latency.recent(redis)
    assert recorded[0]["channel"] == "text" and "agent_total_ms" in recorded[0]


async def test_other_intents_get_a_short_answer(client: httpx.AsyncClient) -> None:
    session_id = await _session(client)
    response = await client.post(
        f"/sessions/{session_id}/turns", json={"text": "tell me a joke"}, headers=KEY
    )
    events = _events(response)
    assert events[0]["text"] == "Sorry, I can only help with your student portal."
    assert events[-1]["intent"] == "out_of_scope"


async def test_a_session_id_alone_is_not_enough_for_text_turns(client: httpx.AsyncClient) -> None:
    session_id = await _session(client)
    response = await client.post(
        f"/sessions/{session_id}/turns",
        json={"text": "attendance", "owner_token": "someone-elses-token"},
        headers=KEY,
    )
    assert response.status_code == 404
    response = await client.post(
        f"/sessions/{session_id}/turns",
        json={"text": "attendance", "owner_token": GOOD_TOKEN},
        headers=KEY,
    )
    assert response.status_code == 200


async def test_unknown_and_ended_sessions(client: httpx.AsyncClient) -> None:
    response = await client.post("/sessions/nope/turns", json={"text": "hi"}, headers=KEY)
    assert response.status_code == 404
    session_id = await _session(client)
    assert (await client.get(f"/sessions/{session_id}", headers=KEY)).json()[
        "first_name"
    ] == "Aarav"
    assert (await client.delete(f"/sessions/{session_id}", headers=KEY)).status_code == 204
    assert (await client.get(f"/sessions/{session_id}", headers=KEY)).status_code == 404


async def test_the_body_cannot_smuggle_extra_fields(client: httpx.AsyncClient) -> None:
    session_id = await _session(client)
    response = await client.post(
        f"/sessions/{session_id}/turns",
        json={"text": "attendance", "reg_no": "24100002"},
        headers=KEY,
    )
    assert response.status_code == 422
