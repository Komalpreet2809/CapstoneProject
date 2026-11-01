"""`POST /voice-tokens`: a LiveKit room token for one voice session (internal only, D-025).

The token admits the browser to its own room, `vs-<session id>`, and dispatches the
VoiceServe agent worker into it with the session id as job metadata. Voice is only offered
when a speech provider is configured (or replay mode is on) and the daily budget allows it.
"""

import json
import secrets
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from livekit.api import AccessToken, RoomAgentDispatch, RoomConfiguration, VideoGrants
from pydantic import BaseModel, ConfigDict, Field

from gateway.settings import Settings
from voiceserve_common.budget import BudgetGuard

TOKEN_TTL = timedelta(minutes=15)


def require_internal_key(
    request: Request, key: Annotated[str | None, Header(alias="X-Internal-Key")] = None
) -> None:
    expected: str = request.app.state.settings.internal_api_key
    if key is None or not secrets.compare_digest(key, expected):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Internal endpoint")


router = APIRouter(tags=["voice"], dependencies=[Depends(require_internal_key)])


class TokenIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=10, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class VoiceAccess(BaseModel):
    url: str
    token: str
    mode: Literal["live", "replay"]


class TokenOut(BaseModel):
    voice: VoiceAccess | None
    reason: Literal["no_provider", "budget"] | None = None


def room_name(session_id: str) -> str:
    return f"vs-{session_id}"


def mint(settings: Settings, session_id: str) -> str:
    return (
        AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(f"student-{session_id[:10]}")
        .with_name("Student")
        .with_ttl(TOKEN_TTL)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name(session_id),
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_room_config(
            RoomConfiguration(
                agents=[
                    RoomAgentDispatch(
                        agent_name=settings.agent_name,
                        metadata=json.dumps({"session_id": session_id}),
                    )
                ]
            )
        )
        .to_jwt()
    )


@router.post("/voice-tokens", response_model=TokenOut)
async def voice_token(body: TokenIn, request: Request) -> TokenOut:
    settings: Settings = request.app.state.settings
    mode = settings.voice_mode
    if mode is None:
        return TokenOut(voice=None, reason="no_provider")
    if mode == "live":
        guard: BudgetGuard = request.app.state.budget
        if await guard.remaining() < settings.min_budget_for_voice_usd:
            return TokenOut(voice=None, reason="budget")
    return TokenOut(
        voice=VoiceAccess(
            url=settings.livekit_public_url,
            token=mint(settings, body.session_id),
            mode="live" if mode == "live" else "replay",
        )
    )
