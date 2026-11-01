"""Registration number + password login, session tokens, lockout after repeated failures."""

from datetime import UTC, datetime, timedelta
from functools import cache

from fastapi import APIRouter, HTTPException, status

from mini_ums_api.conventions import conventions
from mini_ums_api.deps import CurrentSession, Pool
from mini_ums_api.profile import PROFILE_SQL, profile_from_row
from mini_ums_api.schemas import ErrorOut, LoginIn, LoginOut
from mini_ums_api.security import hash_password, new_session_token, token_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

INVALID = "Invalid registration number or password"
LOCKED = "Account locked after too many failed attempts. Try again later or contact the helpdesk."


@cache
def _dummy_hash() -> str:
    # Verified against when the registration number is unknown, so response time does not
    # reveal which registration numbers exist.
    return hash_password("not-a-real-password")


@router.post(
    "/login",
    response_model=LoginOut,
    responses={401: {"model": ErrorOut}, 423: {"model": ErrorOut}},
)
async def login(body: LoginIn, pool: Pool) -> LoginOut:
    policies = conventions().policies
    now = datetime.now(UTC)
    outcome: str
    async with pool.acquire() as conn, conn.transaction():
        row = await conn.fetchrow(PROFILE_SQL + " FOR UPDATE OF s", body.reg_no)
        if row is None:
            verify_password(body.password, _dummy_hash())
            outcome = "invalid"
        elif row["locked_until"] is not None and row["locked_until"] > now:
            outcome = "locked"
        elif not verify_password(body.password, row["password_hash"]):
            failures = row["failed_logins"] + 1
            if failures >= policies.login_max_failures:
                lock_until = now + timedelta(minutes=policies.login_lockout_minutes)
                await conn.execute(
                    "UPDATE students SET failed_logins = 0, locked_until = $2 WHERE reg_no = $1",
                    body.reg_no,
                    lock_until,
                )
                outcome = "locked"
            else:
                await conn.execute(
                    "UPDATE students SET failed_logins = $2 WHERE reg_no = $1",
                    body.reg_no,
                    failures,
                )
                outcome = "invalid"
        else:
            token = new_session_token()
            expires_at = now + timedelta(hours=policies.session_hours)
            await conn.execute(
                "UPDATE students SET failed_logins = 0, locked_until = NULL WHERE reg_no = $1",
                body.reg_no,
            )
            await conn.execute(
                "DELETE FROM sessions WHERE reg_no = $1 AND expires_at <= now()", body.reg_no
            )
            await conn.execute(
                "INSERT INTO sessions (token_hash, reg_no, expires_at) VALUES ($1, $2, $3)",
                token_hash(token),
                body.reg_no,
                expires_at,
            )
            return LoginOut(token=token, expires_at=expires_at, student=profile_from_row(row))
    # Raised after the transaction commits, so failure counters and locks are kept.
    if outcome == "locked":
        raise HTTPException(status.HTTP_423_LOCKED, LOCKED)
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(session: CurrentSession, pool: Pool) -> None:
    await pool.execute("DELETE FROM sessions WHERE token_hash = $1", session.token_hash)
