import math

import pytest
from fakeredis import FakeAsyncRedis

from voiceserve_common import latency


@pytest.mark.parametrize(
    ("values", "pct", "expected"),
    [
        ([100.0], 50, 100.0),
        ([100.0, 200.0, 300.0, 400.0], 50, 200.0),
        ([100.0, 200.0, 300.0, 400.0], 95, 400.0),
        (list(map(float, range(1, 101))), 95, 95.0),
        ([300.0, 100.0, 200.0], 50, 200.0),  # order doesn't matter
    ],
)
def test_percentile_is_nearest_rank(values: list[float], pct: float, expected: float) -> None:
    assert latency.percentile(values, pct) == expected


def test_percentile_of_nothing_is_nan() -> None:
    assert math.isnan(latency.percentile([], 50))


def test_summary_skips_stages_a_turn_did_not_have() -> None:
    turns = [
        {"channel": "voice", "first_audio_ms": 900, "agent_first_sentence_ms": 40},
        {"channel": "voice", "first_audio_ms": 1100, "agent_first_sentence_ms": 60},
        {"channel": "text", "agent_first_sentence_ms": 50},
    ]
    summary = latency.summarize(turns)
    assert summary["first_audio_ms"] == {"n": 2, "p50": 900.0, "p95": 1100.0}
    assert summary["agent_first_sentence_ms"]["n"] == 3
    assert "transcription_ms" not in summary


async def test_records_are_capped_newest_first() -> None:
    redis = FakeAsyncRedis()
    for i in range(latency.KEEP + 5):
        await latency.record(redis, {"turn": i})
    rows = await latency.recent(redis)
    assert len(rows) == latency.KEEP
    assert rows[0] == {"turn": latency.KEEP + 4}
