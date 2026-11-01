"""Print p50/p95 per pipeline stage from recent turns (`make latency`).

Reads the newest turns (up to 1,000) that the gateway worker and orchestrator keep in Redis.
The brief's target is time to first audio p50 < 1.0 s and p95 < 1.6 s on the web.
"""

import asyncio
import os
import sys

import redis.asyncio as aioredis

from voiceserve_common import latency

TARGETS_MS = {"first_audio_ms": (1000, 1600)}


async def main() -> int:
    url = (
        os.environ.get("REDIS_URL")
        or f"redis://localhost:{os.environ.get('REDIS_HOST_PORT', '6380')}/0"
    )
    client = aioredis.from_url(url)
    try:
        turns = await latency.recent(client)
    finally:
        await client.aclose()
    if not turns:
        print("No turns recorded yet. Ask the assistant something first.")
        return 0
    for channel in ("voice", "text"):
        rows = [t for t in turns if t.get("channel") == channel]
        if not rows:
            continue
        print(f"\n{channel} turns: {len(rows)}")
        print(f"  {'stage':<26}{'n':>5}{'p50 ms':>10}{'p95 ms':>10}  target")
        for stage, s in latency.summarize(rows).items():
            target = TARGETS_MS.get(stage)
            verdict = ""
            if target:
                ok = s["p50"] < target[0] and s["p95"] < target[1]
                verdict = f"p50<{target[0]} p95<{target[1]}: {'met' if ok else 'NOT met'}"
            print(f"  {stage:<26}{s['n']:>5.0f}{s['p50']:>10.0f}{s['p95']:>10.0f}  {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
