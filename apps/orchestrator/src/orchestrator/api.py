"""Session and turn endpoints. Internal only: callers present the shared internal key.

`POST /sessions/{id}/turns` streams NDJSON events so the voice worker can speak the first
sentence while the rest are still arriving:

    {"type": "sentence", "text": "..."}       one per sentence, in order
    {"type": "card", "card": {...}}           the on-screen card
    {"type": "done", "turn_id": "...", "timings": {...}}
"""

import json
import secrets
import time
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from orchestrator.sessions import SessionStore, VoiceSession
from orchestrator.ums import MiniUms, UmsUnauthorized, UmsUnavailable
from voiceserve_common import latency


def require_internal_key(
    request: Request, key: Annotated[str | None, Header(alias="X-Internal-Key")] = None
) -> None:
    expected: str = request.app.state.settings.internal_api_key
    if key is None or not secrets.compare_digest(key, expected):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Internal endpoint")


router = APIRouter(tags=["voice"], dependencies=[Depends(require_internal_key)])


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SessionIn(_In):
    api_token: str = Field(min_length=10, max_length=200)
    page_id: str | None = Field(default=None, max_length=80)


class SessionOut(BaseModel):
    session_id: str
    first_name: str
    expires_in: int


class SessionInfo(BaseModel):
    first_name: str
    page_id: str | None


class TurnIn(_In):
    text: str = Field(min_length=1, max_length=500)
    page_id: str | None = Field(default=None, max_length=80)
    channel: Literal["voice", "text"] = "text"
    # Text turns come from the web server on behalf of a logged-in browser; it passes that
    # browser's portal token so a session id alone can't be replayed by someone else.
    owner_token: str | None = Field(default=None, max_length=200)


def _store(request: Request) -> SessionStore:
    store: SessionStore = request.app.state.sessions
    return store


async def _session(request: Request, session_id: str) -> VoiceSession:
    session = await _store(request).get(session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown or expired session")
    return session


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(body: SessionIn, request: Request) -> SessionOut:
    ums: MiniUms = request.app.state.ums
    try:
        profile = await ums.profile(body.api_token)
    except UmsUnauthorized:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Portal session not valid") from None
    except UmsUnavailable:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Portal unavailable") from None
    session = await _store(request).create(
        api_token=body.api_token,
        reg_no=profile["reg_no"],
        first_name=profile["name"].split()[0],
        page_id=body.page_id,
    )
    return SessionOut(
        session_id=session.id,
        first_name=session.first_name,
        expires_in=request.app.state.settings.session_ttl_seconds,
    )


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, request: Request) -> SessionInfo:
    session = await _session(request, session_id)
    return SessionInfo(first_name=session.first_name, page_id=session.page_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(session_id: str, request: Request) -> None:
    await _store(request).delete(session_id)


def _line(event: dict[str, Any]) -> bytes:
    return (json.dumps(event, ensure_ascii=False) + "\n").encode()


@router.post("/sessions/{session_id}/turns")
async def turn(session_id: str, body: TurnIn, request: Request) -> StreamingResponse:
    session = await _session(request, session_id)
    if body.owner_token is not None and not session.owned_by(body.owner_token):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown or expired session")
    graph = request.app.state.graph
    redis = request.app.state.redis
    log = request.app.state.log

    async def events() -> AsyncIterator[bytes]:
        turn_id = uuid.uuid4().hex[:12]
        started = time.perf_counter()
        state = await graph.ainvoke(
            {
                "text": body.text,
                "api_token": session.api_token,
                "first_name": session.first_name,
                "page_id": body.page_id or session.page_id,
            }
        )
        reply = state["reply"]
        first_sentence_ms = round((time.perf_counter() - started) * 1000)
        for sentence in reply.sentences:
            yield _line({"type": "sentence", "text": sentence})
        yield _line({"type": "card", "card": reply.card})
        timings = {
            "agent_first_sentence_ms": first_sentence_ms,
            "agent_total_ms": round((time.perf_counter() - started) * 1000),
        }
        record = {
            "turn_id": turn_id,
            "channel": body.channel,
            "intent": state["intent"].intent,
            **timings,
        }
        log.info("turn", extra=record)
        if body.channel == "text":  # voice turns are recorded by the gateway, with audio stages
            await latency.record(redis, {**record, "at": time.time()})
        yield _line(
            {
                "type": "done",
                "turn_id": turn_id,
                "intent": state["intent"].intent,
                "timings": timings,
            }
        )

    return StreamingResponse(events(), media_type="application/x-ndjson")
