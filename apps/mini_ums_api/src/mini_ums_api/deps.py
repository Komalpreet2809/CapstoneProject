"""Request dependencies: database pool, settings, the authenticated student, idempotency keys."""

import hashlib
import json
from dataclasses import dataclass
from typing import Annotated

import asyncpg
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from mini_ums_api.security import token_hash
from mini_ums_api.settings import Settings

_bearer = HTTPBearer(auto_error=False, description="Session token from POST /auth/login")

IDENTITY_PARAMS = ("student_id", "reg_no")


@dataclass(frozen=True)
class Session:
    reg_no: str
    token_hash: str


def get_pool(request: Request) -> asyncpg.Pool:
    pool: asyncpg.Pool = request.app.state.pool
    return pool


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


async def current_session(
    request: Request,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Session:
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Not signed in", {"WWW-Authenticate": "Bearer"}
        )
    hashed = token_hash(credentials.credentials)
    reg_no = await pool.fetchval(
        "SELECT reg_no FROM sessions WHERE token_hash = $1 AND expires_at > now()", hashed
    )
    if reg_no is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Session expired", {"WWW-Authenticate": "Bearer"}
        )
    # Rule 1: the student comes from the session. Naming anyone else is refused outright.
    for param in IDENTITY_PARAMS:
        claimed = request.query_params.get(param)
        if claimed is not None and claimed != reg_no:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Identity does not match the session")
    return Session(reg_no=reg_no, token_hash=hashed)


CurrentSession = Annotated[Session, Depends(current_session)]
Pool = Annotated[asyncpg.Pool, Depends(get_pool)]
AppSettings = Annotated[Settings, Depends(get_settings)]
IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=128,
        description="Unique per logical request; retries with the same key return the original",
    ),
]


def request_hash(body: BaseModel) -> str:
    canonical = json.dumps(body.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
