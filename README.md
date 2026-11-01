# VoiceServe

A voice-first assistant for a university student portal. A student taps a mic button on any
portal page and speaks in English, Hindi, Punjabi or Hinglish. The assistant reads their data,
files requests after explicit confirmation, tracks those requests, answers policy questions
with citations, and opens any portal page.

It runs against the **Mini UMS**, a self-built portal with fully synthetic data. No real
university system or student data is ever used.

**Status:** M1 (foundation) done: every service starts, reports healthy and is checked in CI.
See [docs/plan.md](docs/plan.md) for milestones and [docs/decisions.md](docs/decisions.md)
for design decisions.

## Quick start

Prerequisites: Docker (with Compose v2), GNU Make, [uv](https://docs.astral.sh/uv/), and
Node 24 for local JS work.

```sh
make up      # build and start everything, wait until healthy, run smoke checks
```

| What | URL |
|---|---|
| Mini UMS (student portal) | http://localhost:3000 |
| Staff dashboard (service status for now) | http://localhost:3001 |
| Mini UMS API docs | http://localhost:8001/docs |
| Orchestrator / gateway API docs | http://localhost:8002/docs, http://localhost:8003/docs |
| Widget bundle | http://localhost:4100/widget.js |

`.env` is optional; copy `.env.example` to change ports or add provider keys later.

On Windows, install the tools with `winget install ezwinports.make` and
`winget install astral-sh.uv` (then open a new terminal), and start Docker Desktop before
running `make up`. The Makefile works from PowerShell, cmd and Git Bash.

## Everyday commands

| Command | Does |
|---|---|
| `make up` / `make down` | Start (and verify) / stop the stack; data is kept |
| `make logs s=gateway` | Follow one service's logs (omit `s=` for all) |
| `make smoke` | Check every service is up and ready |
| `make install` | Install Python and JS dependencies for local development |
| `make test` | Python tests |
| `make lint` | ruff, mypy, eslint, tsc |
| `make fmt` | Auto-format Python |
| `make hooks` | Install pre-commit hooks (secret scan, ruff, file hygiene) |
| `make clean` | Stop and **delete** the database volume |

## Layout

```
apps/
  mini_ums_api/   FastAPI: Mini UMS data API, auth, adapters, seed generator
  mini_ums_web/   Next.js: Mini UMS front end
  widget/         Embeddable voice widget (one framework-free JS file)
  gateway/        Realtime audio: LiveKit, VAD, barge-in
  orchestrator/   LangGraph agent, tools, guardrails, prompts
  dashboard/      Next.js: staff dashboard
libs/common/      Shared Python: settings, masked JSON logging, health checks
rag/              Rulebook ingestion, retrieval, re-ranking          (M5)
language/         Language detection, normalisers, strategies       (M5)
sentiment/        Frustration scoring                                (M6)
eval/             Datasets, metrics, simulator, reports              (M7)
infra/            Dockerfiles, Postgres init
docs/             Plan, decisions, architecture
```

## Ground rules

The full list is in the project brief; the ones that shape every change:

- Safety and correctness first, then measured results, then features.
- Synthetic data only, no real branding, never connect to a real UMS.
- `student_id` comes only from the authenticated session, never from the model.
- Every write is read back and needs an explicit yes; every write is idempotent.
- Secrets live in `.env` only; logs mask IDs, phone numbers, OTPs and tokens.
