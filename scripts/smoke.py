"""Check that every service in the running stack answers and reports ready.

Stdlib only, so it runs on the host or in CI without the uv environment.
Host ports come from the environment or `.env`, with the same defaults as compose.yaml.

    python scripts/smoke.py            # one pass
    python scripts/smoke.py --wait 60  # keep retrying failures for up to 60 s
"""

import argparse
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _dotenv() -> dict[str, str]:
    path = ROOT / ".env"
    if not path.exists():
        return {}
    pairs = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.split("#", 1)[0].strip()
    return pairs


@dataclass
class Target:
    name: str
    url: str
    must_contain: list[str] = field(default_factory=list)


def targets() -> list[Target]:
    env = {**_dotenv(), **os.environ}

    def url(var: str, default: str, path: str) -> str:
        return f"http://localhost:{env.get(var) or default}{path}"

    return [
        Target("mini_ums_api", url("MINI_UMS_API_PORT", "8001", "/ready")),
        Target("orchestrator", url("ORCHESTRATOR_PORT", "8002", "/ready")),
        Target("gateway", url("GATEWAY_PORT", "8003", "/ready")),
        Target("livekit", url("LIVEKIT_HTTP_PORT", "7880", "/")),
        Target("widget", url("WIDGET_PORT", "4100", "/health")),
        Target("widget bundle", url("WIDGET_PORT", "4100", "/widget.js"), ["VoiceServe"]),
        Target("mini_ums_web", url("MINI_UMS_WEB_PORT", "3000", "/api/health")),
        Target(
            "mini_ums_web page",
            url("MINI_UMS_WEB_PORT", "3000", "/"),
            ["Demo – synthetic data", "widget.js"],
        ),
        Target("dashboard", url("DASHBOARD_PORT", "3001", "/api/health")),
    ]


def probe(target: Target) -> str | None:
    """Return None when the target is healthy, else a short reason."""
    try:
        with urllib.request.urlopen(target.url, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return f"HTTP {exc.code}"
    except (urllib.error.URLError, OSError) as exc:
        return str(getattr(exc, "reason", exc))
    missing = [s for s in target.must_contain if s not in body]
    return f"missing {missing}" if missing else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wait", type=float, default=0, help="seconds to keep retrying")
    args = parser.parse_args()

    deadline = time.monotonic() + args.wait
    pending = targets()
    results: dict[str, str | None] = {}
    while True:
        for target in pending:
            results[target.name] = probe(target)
        pending = [t for t in pending if results[t.name] is not None]
        if not pending or time.monotonic() >= deadline:
            break
        time.sleep(2)

    width = max(len(name) for name in results)
    for target in targets():
        reason = results[target.name]
        status = "ok" if reason is None else f"FAIL  {reason}"
        print(f"{target.name:<{width}}  {status:<40} {target.url}")
    failed = [name for name, reason in results.items() if reason is not None]
    print(f"\n{len(results) - len(failed)}/{len(results)} healthy")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
