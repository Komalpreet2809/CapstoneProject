# VoiceServe — milestone plans

Each milestone gets a short plan here before work starts. Design decisions go in
[decisions.md](decisions.md).

---

## M1 — Foundation

**Goal:** a fresh clone runs `make up` and every service starts, reports healthy, and can
reach the services it depends on. CI checks the same thing on every push.

**Done when:** `make up` starts every service and `make smoke` passes; `make test` and
`make lint` pass; CI workflow is in place.

### Services (skeletons only, no features yet)

| Service | Tech | Host port | `/ready` checks |
|---|---|---|---|
| `db` | Postgres 16 + pgvector | 5433 | `pg_isready` |
| `redis` | Redis 7.4 | 6380 | `PING` |
| `livekit` | LiveKit server (dev mode) | 7880–7882 | HTTP root |
| `mini_ums_api` | FastAPI | 8001 | Postgres reachable, `vector` extension installed |
| `orchestrator` | FastAPI | 8002 | Redis + `mini_ums_api` reachable |
| `gateway` | FastAPI | 8003 | `orchestrator` + LiveKit reachable |
| `widget` | TypeScript → one JS bundle, served by nginx | 4100 | `/health` |
| `mini_ums_web` | Next.js + Tailwind | 3000 | `/api/health`; page embeds the widget |
| `dashboard` | Next.js + Tailwind | 3001 | `/api/health`; page shows every service's status |

Host ports for Postgres and Redis avoid 5432/6379, which other local stacks already use.
All host ports can be overridden in `.env`.

### Work items

1. Repo skeleton following the brief's layout (§11), `.gitignore`, `.gitattributes` (LF),
   `.editorconfig`, `.dockerignore`.
2. Python: uv workspace pinned to 3.11; one lockfile; ruff, mypy and pytest configured at
   the root. Shared package `libs/common` for settings, JSON logging and log masking.
3. Python service skeletons with `/health` (liveness) and `/ready` (dependency checks).
4. JS skeletons: two Next.js apps and the framework-free widget bundle.
5. `compose.yaml` with healthchecks and `depends_on: service_healthy`, so `make up` returns
   only when everything is healthy.
6. `Makefile`: `help up down restart logs ps smoke install test lint fmt hooks clean`
   (`lint` includes type checking).
7. `.env.example` listing every variable the project will need, with safe local defaults
   and empty provider keys.
8. CI (GitHub Actions): Python lint/type/test, JS lint/build per app, secret scan
   (gitleaks), and a compose smoke test.
9. pre-commit hooks: gitleaks, ruff, basic file hygiene.
10. Docs: this plan, `decisions.md`, `architecture.md`, README quick start.

### Tests in M1

- Log masking (rule 11 starts now): table-driven tests for phone numbers, numeric IDs,
  OTP-length codes, sensitive keys in structured logs, nested data.
- Settings: defaults, `LANG_STRATEGY` validation, budget must be non-negative.
- `/health` and `/ready` for each Python service, with dependency checks stubbed
  (healthy, failing, and raising).
- `scripts/smoke.py` against the running stack.

### Deliberately not in M1

- Database schema, seed data, real API endpoints, auth → **M2**.
- Provider interfaces, budget-cap guard, replay mode, Langfuse tracing → **M3** (first
  paid provider call happens there).
- Student ID format in the masker is generic until `conventions.yaml` defines it in **M2**.

### Risks

- WebRTC UDP through Docker Desktop on Windows can be unreliable. M1 only checks that
  LiveKit starts; real audio is tested in M3, with LiveKit Cloud as the fallback.

### Outcome (2026-11-01)

Done. Verified on the Windows dev machine:

- `make up` builds all images and returns with 9/9 smoke checks passing; the dashboard shows
  6/6 services ready; `/ready` confirms `vector 0.8.7` in Postgres.
- `make test`: 72 passed. `make lint`: ruff, mypy (strict), eslint, tsc all clean. The same
  Python checks pass in a clean Linux container (CI parity).
- Headless Chrome: the Mini UMS page loads `widget.js` cross-origin and the mic button renders
  bottom-right; the demo banner shows on every page.
- Live container logs mask query-string IDs and phone numbers (`student_id=****78`).
- Every app container runs as a non-root user.
- Pre-commit hooks pass on the whole tree, and gitleaks blocks a staged fake token.
- CI workflow passes `actionlint`; it has not run on GitHub yet (repo not pushed).

### Open questions before M2

- **Where OTP fits on the web.** The brief asks for OTP logic and expired-OTP edge cases, and
  the agent graph has "authenticate (if needed)", but web users are already logged in to the
  Mini UMS. Options: OTP as a login step; OTP as step-up before writes; OTP only on the phone
  channel (stretch).
- **Student ID format** for `conventions.yaml` (e.g. 8-digit numeric vs. prefixed like
  `DEMO001`). It drives the log masker, login and the seed generator.
