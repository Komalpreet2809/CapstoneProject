"""Daily spend cap for paid providers (brief §14, D-028).

Every paid call first reserves its estimated cost. The reservation is atomic: the amount is
added with INCRBYFLOAT and taken back if the new total passes the cap, so concurrent calls can
never push the day's spend over `DAILY_BUDGET_USD`. After the call, `settle` replaces the
estimate with the actual cost. Days follow campus time (IST).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis

IST = timezone(timedelta(hours=5, minutes=30))
KEY_TTL_SECONDS = 3 * 24 * 3600


class BudgetExceeded(Exception):
    """Today's paid-provider spend would pass the daily cap."""


@dataclass(frozen=True)
class Reservation:
    key: str
    amount: float


def _today() -> str:
    return datetime.now(IST).date().isoformat()


class BudgetGuard:
    def __init__(self, redis: aioredis.Redis, daily_cap_usd: float) -> None:
        self._redis = redis
        self._cap = daily_cap_usd

    @staticmethod
    def key(day: str | None = None) -> str:
        return f"budget:spent:{day or _today()}"

    async def spent_today(self) -> float:
        value = await self._redis.get(self.key())
        return float(value) if value is not None else 0.0

    async def remaining(self) -> float:
        return max(0.0, self._cap - await self.spent_today())

    async def reserve(self, estimate_usd: float) -> Reservation:
        key = self.key()
        if estimate_usd <= 0:
            return Reservation(key, 0.0)
        total = float(await self._redis.incrbyfloat(key, estimate_usd))
        await self._redis.expire(key, KEY_TTL_SECONDS)
        if total > self._cap:
            await self._redis.incrbyfloat(key, -estimate_usd)
            raise BudgetExceeded(f"daily budget of ${self._cap:.2f} reached")
        return Reservation(key, estimate_usd)

    async def settle(self, reservation: Reservation, actual_usd: float) -> None:
        """Swap the estimate for the real cost (may be lower or slightly higher)."""
        delta = actual_usd - reservation.amount
        if delta:
            await self._redis.incrbyfloat(reservation.key, delta)
            await self._redis.expire(reservation.key, KEY_TTL_SECONDS)

    async def record(self, actual_usd: float) -> None:
        """Spend that couldn't be reserved up front (metered streams such as STT audio)."""
        if actual_usd > 0:
            await self.settle(Reservation(self.key(), 0.0), actual_usd)
