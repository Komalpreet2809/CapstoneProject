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

---

## M2 — Mini UMS

**Goal:** opening `localhost:3000` feels like our university's UMS (same structure, layout
and flows) with an original identity: own name (**Univra**), logo and colours.

**Done when:** login → dashboard looks and navigates like the real UMS layout, every menu
entry opens, and the RMS flow works end to end on synthetic data. Plus the brief's M2
criteria: API tests pass and the API contract is frozen.

**Reference:** `docs/reference/ums-structure.md` records the real portal's layout, flows and
menu groups (observed 2026-11-01). The menu catalogue in `conventions.yaml` follows it; page
specs for the inner pages (attendance, timetable, fees, …) are still to come.

**Progress (2026-11-01):** every "done when" item is met.

- Backend: 160 Python tests, including the contract drift test against the frozen
  `docs/api/openapi.json` (`make openapi` regenerates it after a deliberate change).
- Front end built to match the reference: login; shell (announcement strip, right-aligned
  mega-menus, search with Quick Links pins, student block, labelled rail); dashboard
  (Important Links, banner, Happening, My Messages, My Courses, Fee, Pending Assignments,
  Events, Placement Details, Campus Drive pop-up); standalone RMS (Log Request, RMS
  History); shared placeholder page.
- Browser tests: 9 Playwright tests (`make e2e`, re-seeds first) cover login/lockout/logout,
  redirect-and-return, the drive pop-up and dashboard cards, mega-menu → placeholder,
  search + Quick Links, RMS log → duplicate → note, and feedback that reopens a request.
- CI now runs the API tests against a Postgres service (they were silently skipped before)
  and the browser tests after the Compose smoke test. Neither has run on GitHub yet.

Deferred: the Important Announcements board (needs categorised notices in the API).

### Answers to the M1 open questions

- **OTP:** login is registration number + password (per the M2 spec). OTP is not part of
  web login; where it fits (agent step-up before writes, or phone only) is decided in M4.
- **IDs:** placeholder registration number = 8 digits (2-digit intake year + 6-digit
  serial). Replaced from `docs/reference/` when the real format arrives.

### Backend (`mini_ums_api`)

1. **Schema** as numbered SQL migrations applied on startup: students, sessions, courses,
   enrollments, attendance, marks, timetable, fees, assignments, exams and seating, tickets
   and ticket events, hostel leaves, announcements, news, events, messages, placement drives.
2. **Auth:** registration number + password (scrypt), opaque session tokens (only a hash
   stored), 8-hour expiry, lockout after 5 failures, password age shown as days to expiry.
3. **Identity (rule 1):** every personal route is `/me/...` and takes the student from the
   token. A `student_id`/`reg_no` in the query that doesn't match → 403; request bodies
   forbid unknown fields.
4. **RMS:** declarations must be accepted (version recorded on the ticket, rule 10);
   `Idempotency-Key` header required (rule 3); a similar open ticket → 409 with that ticket so
   the UI can offer "add a note" instead (rule 7); ticket number = 4-digit sequence + Damm
   check digit (rule 9), shown as `DEPT/Mon-YY/NNNNN`; history with counts; notes; feedback
   after closure, where "not resolved" reopens the ticket.
5. **Read APIs for every MVP feature** (attendance with % computed in code, timetable,
   fees, exams + seating, assignments, hostel leave), so the contract can freeze now even
   though their dedicated pages wait for page specs.
6. **Seed generator:** fixed seed, dates relative to an anchor day, correlated
   distributions, deliberate edge cases, six stable demo personas. Runs automatically when
   the database is empty; `make seed` re-seeds.
7. **Contract:** `docs/api/openapi.json` is generated from the app; a test fails if the
   app drifts from it.

### Front end (`mini_ums_web`)

1. Login page (original design, dev-only demo account hint).
2. App shell: announcement ribbon, top bar with logo, five mega-menus (full-width grouped
   panels), search over all menu entries, student identity block, narrow icon sidebar.
3. Dashboard: shortcut pills, banner carousel, Happening, My Messages, My Courses (with
   attendance rings), Fee, Pending Assignments, Events, placement-drive modal, password
   expiry notice.
4. RMS module with its own header: Log Request (declarations → form → duplicate prompt →
   confirmation) and RMS History (counters, cards, feedback).
5. One shared placeholder page for every other menu entry.
6. Voice widget on every page (unchanged).

The browser never sees the session token: it lives in an httpOnly cookie, and Next.js
server code calls the API.

### Tests

- Unit: Damm check digit, request-ID format/parse, password hashing, lockout, seed
  determinism and distributions.
- API (against a real Postgres): auth, identity guard, every `/me` route, RMS create /
  idempotency / duplicate / notes / feedback-reopen, hostel leave validation.
- Contract: generated OpenAPI equals the committed file.
- End to end (Playwright): login → dashboard → mega-menu → placeholder page → RMS log
  request → history → feedback.

### Not in M2

Dedicated pages for attendance, timetable, fees, exams and hostel leave (waiting for page
specs); OTP; staff-side ticket handling (M6); adapter clients for the agent (M3/M4).

---

## M3 — Voice MVP (English, one Ask feature)

**Goal:** a student taps the mic on any Univra page, asks about their attendance in English,
and hears the answer while a card with the numbers appears. They can interrupt it.

**Done when (brief):** spoken question → spoken answer + card; barge-in works; latency logged.

**The Ask feature:** course-wise attendance ("What's my attendance?", "Am I short in Computer
Networks?", "How many classes can I miss in CSE326?"). Percentages and threshold comparisons
already come from the API, computed in code.

### How a turn flows

1. The widget asks the host page for a voice session: `POST /api/voice/session` on the Mini
   UMS origin. The Next.js route reads the httpOnly cookie, so the API token never reaches the
   browser or the widget.
2. The gateway checks the token with the orchestrator, then returns a LiveKit room token and an
   opaque session id. The orchestrator keeps the session in Redis: the API token, student,
   page and language.
3. The widget joins the LiveKit room with the mic (push-to-talk). A LiveKit Agents worker joins
   too: Silero VAD + end-of-turn detection, then streaming speech-to-text, sending live captions
   to the widget.
4. On end of turn the worker sends the transcript to the orchestrator
   (`POST /sessions/{id}/turns`). The graph runs classify → attendance → respond and streams
   sentences, then a card.
5. The worker speaks each sentence as it arrives (sentence-level streaming TTS) and forwards
   the card over the data channel. The widget renders it.
6. **Barge-in:** the student starts speaking (or taps the mic) → playback stops, the
   orchestrator stream is cancelled and the turn is marked interrupted.
7. **Text fallback:** typing in the panel goes through `POST /api/voice/text` to the same
   orchestrator turn API. It works even when WebRTC doesn't.

### Work items

1. **Providers** (`libs/common`): interfaces for STT, TTS and LLM; `live` and `replay`
   implementations selected by `REPLAY_MODE`; a price table; a **budget guard** that checks
   today's spend in Redis before every paid call and records the actual cost after it.
2. **Orchestrator:** a session store (Redis, 1 h TTL); a Mini UMS adapter (the agent never
   touches the database); a LangGraph graph (classify → attendance → respond, plus polite
   refusals for out-of-scope or not-yet-supported requests); deterministic course matching
   (codes like "cse 326", "CSE-326", titles); replies **templated from tool output**; the
   streaming turn API.
3. **Gateway:** `POST /sessions` (internal key, mints the LiveKit token); a LiveKit Agents
   worker (a separate Compose service from the same image) that wires VAD, STT, the
   orchestrator and TTS, handles interruptions and records per-stage timestamps.
4. **Widget:** states idle → listening (live captions) → thinking → speaking → done;
   push-to-talk; answer cards; text input; bottom sheet on mobile. livekit-client is bundled,
   so it stays one script.
5. **Mini UMS web:** the voice session and text routes; a real **Attendance page** (the card
   links to it; it's an M2 carry-over, see below).
6. **Latency:** per turn, end of utterance, final transcript, the agent's first sentence and
   first TTS audio, summed into time to first audio. They go to JSON logs and a Redis list;
   `make latency` prints p50/p95 against the target.
7. **Tracing:** Langfuse Cloud when its keys are set; otherwise logs only (decides D-010).

### Tests

- Unit: budget guard (under, at and over the cap; day rollover; concurrent spends), provider
  selection, sentence splitter, course matcher (table-driven), attendance reply templates (every
  number traced to tool output), intent schema, session store expiry, latency maths.
- API: session creation (bad token → 401; the token never appears in a response), the turn
  stream (sentences then card), out-of-scope refusal, cancellation.
- End to end (replay mode, in CI): Playwright text-fallback question → card; a voice question
  fed into Chrome's fake microphone from a WAV fixture → spoken-answer events + card.
- Manual with live providers: speak, hear, interrupt; latency table recorded in this plan.

### Carried over from M2

The brief's M2 asked for real pages for the MVP features. Univra has placeholders for them.
M3 builds **Attendance** (the voice card links to it); timetable, fees, exams, assignments and
hostel leave follow in M4, where "navigate" needs them.

### Not in M3

Other Ask features, Do/Track/Learn and confirm-before-write (M4); Hindi, Punjabi and Hinglish
(M5); frustration detection and hand-off (M6); evaluation report (M7).

### What only you can do

Create accounts and put keys in `.env`: `DEEPGRAM_API_KEY` (speech-to-text and text-to-speech),
`ANTHROPIC_API_KEY` (the LLM) and, optionally, `LANGFUSE_*`. Until then everything runs and is
tested in replay mode, which is free. With keys set, the daily cap (`DAILY_BUDGET_USD`, $5)
still applies.

### Risks

- WebRTC UDP through Docker Desktop on Windows (D-009): if audio fails locally, switch
  `LIVEKIT_URL` to LiveKit Cloud (free tier) without code changes.
- Time to first audio target p50 < 1.0 s: templated replies help; measure before optimising.

### Outcome (2026-11-01)

Done in replay mode; live providers wait for keys.

- **Voice path, end to end (replay providers):** a Playwright test speaks into Chrome's fake
  microphone. The question travels through LiveKit to the worker (Silero VAD, replay STT), the
  orchestrator answers, replay TTS "speaks" it and the widget shows the transcript, reply and
  attendance card. Tapping the mic while it speaks interrupts and listens again (barge-in).
  CI runs this test with `REPLAY_MODE=true`.
- **Latency logged:** first voice turn: 621 ms to first audio (end of utterance 580, agent
  first sentence 17, TTS first audio 25). Text turns: agent p50 2 ms, p95 11 ms. The 580 ms
  is the VAD's silence wait; real STT/TTS will add their own time, measured once keys exist.
- **Text fallback:** typed questions stream the same answer and card (Playwright tests).
- **Tests:** 259 Python tests (budget guard, latency maths, course matcher, rules classifier,
  reply grounding, Claude classifier with the budget, orchestrator API, gateway tokens, the
  orchestrator-as-LLM stream); 13 Playwright tests (the voice one needs replay mode).
- **Found and fixed on the way:** a header layout shift switched mega-menus under a resting
  mouse; session-expired redirects pointed at the server's bind address (`0.0.0.0`).
- **Not verified:** Deepgram speech and Claude intent with real keys (none configured).
  Add `DEEPGRAM_API_KEY` and `ANTHROPIC_API_KEY` to `.env`, then `make up` and try the mic.
