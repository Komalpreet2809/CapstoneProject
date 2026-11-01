"""Adapter to the Mini UMS API. The agent never touches the database (architecture.md).

Calls are made as the student: their own session token, kept server-side with the voice
session, is sent as the bearer token, so the API's identity checks (rule 1) apply unchanged.
"""

from typing import Any

import httpx


class UmsUnauthorized(Exception):
    """The student's portal session is no longer valid."""


class UmsUnavailable(Exception):
    """The Mini UMS API couldn't be reached or answered with an error."""


class MiniUms:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def _get(self, path: str, token: str) -> Any:
        try:
            response = await self._client.get(path, headers={"Authorization": f"Bearer {token}"})
        except httpx.HTTPError as exc:
            raise UmsUnavailable(type(exc).__name__) from exc
        if response.status_code == 401:
            raise UmsUnauthorized
        if response.status_code >= 400:
            raise UmsUnavailable(f"HTTP {response.status_code}")
        return response.json()

    async def profile(self, token: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._get("/me", token)
        return result

    async def attendance(self, token: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = await self._get("/me/attendance", token)
        return result
