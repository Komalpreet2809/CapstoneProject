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
