# Decision log

One entry per design decision: what was decided, why, and when to revisit. Newest at the
bottom. Status is **Accepted** unless marked **Provisional** (to be confirmed in a later
milestone).

---

### D-001 — The project brief is the spec; the PDF guide is reference only
*M1 · 2026-11-01 · Accepted*

The earlier "Detailed Implementation Guide" PDF differs from the current brief. Where they
conflict, the brief wins. The PDF is still useful for patterns: schema ideas, latency budget,
normaliser tables, evaluation dataset formats.

| Topic | PDF guide | Brief (followed) |
|---|---|---|
| Admissions RAG agent, eligibility engine | CORE | Out of scope |
| Phone channel (Twilio) | CORE | Stretch |
| Gate passes, OASIS placements, mentor booking | CORE tools | Replaced by hostel leave; others out |
| RAG corpus | Public admission brochures | UMS policy documents (attendance, exam, hostel) |
| Front end | Staff dashboard only | Mini UMS web + embedded widget + staff dashboard |
| Mock service | `apps/tools_api` | `apps/mini_ums_api` |
| Auth | Student ID + OTP inside every call | Mini UMS login session; where OTP fits on the web (login step, the agent's "authenticate if needed" node, or both) is an open question for M2 |

The PDF also uses a real university's name; nothing in the code or UI does (brief §6.1).

### D-002 — Repository layout
*M1 · 2026-11-01 · Accepted*

Follows brief §11, with three additions:
- `libs/common` — shared Python code (settings, JSON logging, log masking, health checks).
  Every service needs these, and copying them would drift.
- `infra/docker/` — one Dockerfile per *kind* of service (Python, Next.js) instead of one per
  app, so the three Python services and two Next.js apps can't drift apart.
- `compose.yaml` and `Makefile` at the root (not in `infra/`), so `docker compose` and `make`
  work without flags. GitHub requires workflows in `.github/workflows/`.

### D-003 — Python: uv workspace pinned to 3.11
*M1 · 2026-11-01 · Accepted*

One uv workspace, one `uv.lock`, `src/` layout, Python pinned to 3.11 (`.python-version`,
`requires-python = ">=3.11,<3.12"`). uv downloads 3.11 itself, so the system Python (3.13 on
the dev machine) doesn't matter. Docker images build from the same lockfile with
`uv sync --frozen --package <service>`.

Library packages get a `voiceserve_` prefix (`voiceserve_rag`, `voiceserve_eval`, ...)
because names like `eval` and `language` are too generic to import safely. Service packages
keep their directory names (`mini_ums_api`, `orchestrator`, `gateway`).

### D-004 — JS apps are independent npm projects
*M1 · 2026-11-01 · Accepted*

`mini_ums_web`, `dashboard` and `widget` each have their own `package-lock.json`, with no npm
workspace. They share almost no code (the widget is deliberately framework-free), and
independent projects give simple, self-contained Docker builds. Revisit if shared UI code
appears between the two Next.js apps.

### D-005 — Next.js 16 + Tailwind 4 with framework defaults
*M1 · 2026-11-01 · Accepted*

Versions checked on npm on 2026-11-01: Next 16.4.3, React 19.3, Tailwind 4.3. We keep what
`create-next-app` turns on (Cache Components, partial prefetching, Turbopack Tailwind loader)
rather than fighting the defaults. Consequence: anything read at request time (env vars,
service status) must sit behind `await connection()` inside a `<Suspense>` boundary.
TypeScript stays on 5.x (TS 7 is out but Next 16 ships with 5.x).

### D-006 — Exact image tags
*M1 · 2026-11-01 · Accepted*

No `latest` tags. Pinned: `python:3.11.18-slim-bookworm`, `node:24.22.2-alpine`,
`nginx:1.30.6-alpine`, `pgvector/pgvector:0.8.7-pg16`, `redis:7.4.12-alpine`,
`livekit/livekit-server:v1.13.11`, `ghcr.io/astral-sh/uv:0.13.6`. Bumped deliberately.

### D-007 — Host ports avoid common clashes
*M1 · 2026-11-01 · Accepted*

Postgres is exposed on **5433** and Redis on **6380**, because 5432/6379 are often taken by
other local stacks (they were on the dev machine). The widget uses **4100** (4000 was taken).
Every host port can be overridden in `.env`. Inside the Compose network, services use the
standard ports.

### D-008 — One Postgres (with pgvector) for UMS data and rulebook embeddings
*M1 · 2026-11-01 · Accepted*

Matches the brief's stack. One database to run, back up and seed. The `vector` extension is
created on first start (`infra/postgres/init/`), and `mini_ums_api` won't report ready until
it exists.

### D-009 — LiveKit: self-hosted dev server locally
*M1 · 2026-11-01 · Provisional — confirm in M3*

Compose runs `livekit-server --dev` (placeholder keys `devkey`/`secret`; TCP 7881, UDP 7882),
so the stack runs offline with no account. Risk: WebRTC UDP through Docker Desktop on Windows
can be unreliable. M3 tests real audio; if it fails, we switch `LIVEKIT_URL` to LiveKit Cloud
without code changes.

### D-010 — Langfuse is not in Compose yet
*M1 · 2026-11-01 · Provisional — decide in M3*

Self-hosted Langfuse v3 needs ClickHouse, MinIO, Redis and Postgres (four or more extra
containers). Tracing starts in M3, so the choice (Langfuse Cloud, self-host behind a Compose
profile, or OpenTelemetry) is made there. `.env.example` already has the keys.

### D-011 — The widget is served from its own origin
*M1 · 2026-11-01 · Accepted*

The widget is a framework-free TypeScript bundle (esbuild, IIFE, ~3 KB) served by nginx on
its own port, with CORS. The Mini UMS loads it as a third-party script, the way a real UMS
would. It renders inside a Shadow DOM so host-page CSS and widget CSS can't affect each other.
The script URL is read at request time (`WIDGET_URL`), so one image works in any environment.

### D-012 — `/health` vs `/ready`, and `make up` waits for both
*M1 · 2026-11-01 · Accepted*

Every Python service exposes `/health` (process alive, no I/O) and `/ready` (checks its real
dependencies concurrently with a 2 s timeout; 503 if any fail). Compose healthchecks poll
`/ready`, and `depends_on: service_healthy` orders startup. `make up` runs
`docker compose up --wait` and then `scripts/smoke.py`, so it only succeeds when every service
is genuinely usable.

### D-013 — Least-privilege environment per service
*M1 · 2026-11-01 · Accepted*

Compose doesn't pass `.env` wholesale (`env_file`) to containers. Each service lists the
variables it needs, so a provider key added for the gateway never reaches the Mini UMS API.
Python services read settings from the environment only (pydantic-settings).

### D-014 — Log masking from day one (rule 11)
*M1 · 2026-11-01 · Accepted*

Every log line is JSON on stdout and goes through `voiceserve_common.masking` first,
including uvicorn access logs, which contain query strings. Free text: Indian mobile numbers in
common formats and any run of 6+ digits are masked to `****` + last two digits. Fixed width,
so the length isn't revealed. Structured fields: secrets (`password`, `otp`, `*_token`,
`authorization`, ...) become `[REDACTED]`; identifiers (`student_id`, `phone*`, ...) keep only
their last two characters. Short numbers (ticket IDs, dates, times, latencies) survive, so logs
stay useful. Known gap: numbers spoken as words in transcripts aren't caught. The
student-ID pattern is tightened in M2 once `conventions.yaml` fixes the ID format.

### D-015 — Secret scanning in two places
*M1 · 2026-11-01 · Accepted*

gitleaks runs as a pre-commit hook (`make hooks`) and on full git history in CI. Verified
locally: a staged fake GitHub token is blocked.

### D-016 — GNU Make on Windows; recipes portable across shells
*M1 · 2026-11-01 · Accepted*

`make` is the one-command interface (brief M1). On Windows it's GNU Make 4.4.1 via winget
(`ezwinports.make`). Recipes only call real executables (`docker`, `uv`, `npm`) with plain
arguments, and `help` uses make's `$(info)`, so the same Makefile works under `sh` and
`cmd.exe`. Tested from Git Bash and PowerShell.

### D-017 — LF line endings everywhere
*M1 · 2026-11-01 · Accepted*

`.gitattributes` forces LF. Dockerfiles, shell snippets and the Makefile run inside Linux
containers; CRLF would break them on Windows machines with `core.autocrlf=true`.
