"""Voice sessions in Redis (brief §6: session state in Redis).

A session ties a widget conversation to the student's portal session token, which stays here
and is never sent to the browser (D-025). Sessions expire after an hour without activity.
"""

import hashlib
import json
import secrets
import time
from dataclasses import asdict, dataclass

import redis.asyncio as aioredis


def token_fingerprint(api_token: str) -> str:
    return hashlib.sha256(api_token.encode()).hexdigest()


@dataclass(frozen=True)
class VoiceSession:
    id: str
    api_token: str
    reg_no: str
    first_name: str
    page_id: str | None
    created_at: float

    def owned_by(self, api_token: str) -> bool:
        return secrets.compare_digest(
            token_fingerprint(api_token), token_fingerprint(self.api_token)
        )


class SessionStore:
    def __init__(self, redis: aioredis.Redis, ttl_seconds: int) -> None:
        self._redis = redis
        self._ttl = ttl_seconds

    @staticmethod
    def _key(session_id: str) -> str:
        return f"voice:session:{session_id}"

    async def create(
        self, *, api_token: str, reg_no: str, first_name: str, page_id: str | None
    ) -> VoiceSession:
        session = VoiceSession(
            id=secrets.token_urlsafe(18),
            api_token=api_token,
            reg_no=reg_no,
            first_name=first_name,
            page_id=page_id,
            created_at=time.time(),
        )
        await self._redis.set(self._key(session.id), json.dumps(asdict(session)), ex=self._ttl)
        return session

    async def get(self, session_id: str) -> VoiceSession | None:
        raw = await self._redis.get(self._key(session_id))
        if raw is None:
            return None
        await self._redis.expire(self._key(session_id), self._ttl)  # sliding expiry
        return VoiceSession(**json.loads(raw))

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))
