import asyncio

import pytest
from fakeredis import FakeAsyncRedis

from voiceserve_common.budget import BudgetExceeded, BudgetGuard
from voiceserve_common.pricing import llm_cost, stt_cost, tts_cost


@pytest.fixture
def redis() -> FakeAsyncRedis:
    return FakeAsyncRedis()


async def test_reserve_under_the_cap(redis: FakeAsyncRedis) -> None:
    guard = BudgetGuard(redis, daily_cap_usd=1.0)
    await guard.reserve(0.4)
    assert await guard.spent_today() == pytest.approx(0.4)
    assert await guard.remaining() == pytest.approx(0.6)


async def test_reserving_exactly_up_to_the_cap_is_allowed(redis: FakeAsyncRedis) -> None:
    guard = BudgetGuard(redis, daily_cap_usd=1.0)
    await guard.reserve(0.5)
    await guard.reserve(0.5)
    assert await guard.remaining() == pytest.approx(0.0)


async def test_over_the_cap_is_refused_and_rolled_back(redis: FakeAsyncRedis) -> None:
    guard = BudgetGuard(redis, daily_cap_usd=1.0)
    await guard.reserve(0.9)
    with pytest.raises(BudgetExceeded):
        await guard.reserve(0.2)
    assert await guard.spent_today() == pytest.approx(0.9)


async def test_zero_cap_refuses_every_paid_call(redis: FakeAsyncRedis) -> None:
    guard = BudgetGuard(redis, daily_cap_usd=0)
    with pytest.raises(BudgetExceeded):
        await guard.reserve(0.0001)


async def test_free_calls_never_touch_the_budget(redis: FakeAsyncRedis) -> None:
    guard = BudgetGuard(redis, daily_cap_usd=0)
    await guard.reserve(0)  # replay mode
    assert await redis.get(guard.key()) is None


async def test_settle_replaces_the_estimate_with_the_actual(redis: FakeAsyncRedis) -> None:
    guard = BudgetGuard(redis, daily_cap_usd=1.0)
    reservation = await guard.reserve(0.30)
    await guard.settle(reservation, 0.05)
    assert await guard.spent_today() == pytest.approx(0.05)


async def test_metered_spend_is_recorded(redis: FakeAsyncRedis) -> None:
    guard = BudgetGuard(redis, daily_cap_usd=1.0)
    await guard.record(0.25)
    await guard.record(0)
    assert await guard.spent_today() == pytest.approx(0.25)


async def test_concurrent_reservations_never_pass_the_cap(redis: FakeAsyncRedis) -> None:
    guard = BudgetGuard(redis, daily_cap_usd=1.0)

    async def attempt() -> bool:
        try:
            await guard.reserve(0.3)
        except BudgetExceeded:
            return False
        return True

    results = await asyncio.gather(*(attempt() for _ in range(10)))
    assert sum(results) == 3
    assert await guard.spent_today() == pytest.approx(0.9)


async def test_each_day_has_its_own_total(redis: FakeAsyncRedis) -> None:
    guard = BudgetGuard(redis, daily_cap_usd=1.0)
    await redis.set(BudgetGuard.key("2026-10-31"), 1.0)  # yesterday spent everything
    await guard.reserve(0.5)
    assert await guard.spent_today() == pytest.approx(0.5)
    assert await redis.ttl(guard.key()) > 0  # old days expire


@pytest.mark.parametrize(
    ("model", "tokens_in", "tokens_out", "usd"),
    [
        ("claude-haiku-5-5", 1_000_000, 0, 0.10),
        ("claude-haiku-5-5", 0, 1_000_000, 0.50),
        ("claude-haiku-5-5", 500, 100, 0.0001),
        ("some-new-model", 0, 1_000_000, 20.00),  # unknown: priced like the dearest
    ],
)
def test_llm_cost(model: str, tokens_in: int, tokens_out: int, usd: float) -> None:
    assert llm_cost(model, tokens_in, tokens_out) == pytest.approx(usd)


def test_speech_costs() -> None:
    assert stt_cost(60) == pytest.approx(0.0077)
    assert tts_cost(1000) == pytest.approx(0.030)
