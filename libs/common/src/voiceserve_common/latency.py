"""Per-turn latency records (brief: "latency logged"; target time to first audio p50 < 1.0 s).

Each finished turn stores its stage durations in milliseconds. The newest 1,000 are kept in a
Redis list for `make latency`; every record is also logged as JSON by the caller.
"""

import json
import math
from collections.abc import Iterable, Mapping
from typing import Any

import redis.asyncio as aioredis

KEY = "latency:turns"
KEEP = 1000

# Stage names, in pipeline order. A turn may have only some of them (text turns have no audio).
STAGES = (
    "end_of_utterance_ms",  # user stopped speaking -> turn committed (VAD/end-of-turn)
    "transcription_ms",  # end of speech -> final transcript
    "agent_first_sentence_ms",  # transcript received -> first reply sentence (orchestrator)
    "tts_first_audio_ms",  # first sentence -> first synthesized audio
    "first_audio_ms",  # user stopped speaking -> first audio out (the headline number)
    "agent_total_ms",  # whole orchestrator turn
)


async def record(redis: aioredis.Redis, turn: Mapping[str, Any]) -> None:
    await redis.lpush(KEY, json.dumps(turn, separators=(",", ":")))
    await redis.ltrim(KEY, 0, KEEP - 1)


async def recent(redis: aioredis.Redis, limit: int = KEEP) -> list[dict[str, Any]]:
    rows = await redis.lrange(KEY, 0, limit - 1)
    return [json.loads(r) for r in rows]


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile, which never invents a value between two measurements."""
    if not values:
        return math.nan
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


def summarize(turns: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    rows = list(turns)
    summary: dict[str, dict[str, float]] = {}
    for stage in STAGES:
        values = [float(t[stage]) for t in rows if isinstance(t.get(stage), int | float)]
        if values:
            summary[stage] = {
                "n": len(values),
                "p50": percentile(values, 50),
                "p95": percentile(values, 95),
            }
    return summary
