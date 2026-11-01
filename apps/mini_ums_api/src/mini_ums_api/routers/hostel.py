"""Hostel leave: apply (idempotent) and track."""

import asyncpg
from fastapi import APIRouter, HTTPException, Response, status

from mini_ums_api.conventions import conventions
from mini_ums_api.deps import CurrentSession, IdempotencyKey, Pool, request_hash
from mini_ums_api.rules import campus_today
from mini_ums_api.schemas import ErrorOut, LeaveCreate, LeaveOut

router = APIRouter(prefix="/me/hostel-leaves", tags=["hostel"])


def leave_out(r: asyncpg.Record) -> LeaveOut:
    return LeaveOut(
        id=r["id"],
        from_date=r["from_date"],
        to_date=r["to_date"],
        days=(r["to_date"] - r["from_date"]).days + 1,
        reason=r["reason"],
        status=r["status"],
        channel=r["channel"],
        created_at=r["created_at"],
    )


@router.get("", response_model=list[LeaveOut])
async def list_leaves(session: CurrentSession, pool: Pool) -> list[LeaveOut]:
    rows = await pool.fetch(
        "SELECT * FROM hostel_leaves WHERE reg_no = $1 ORDER BY created_at DESC, id DESC",
        session.reg_no,
    )
    return [leave_out(r) for r in rows]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=LeaveOut,
    responses={
        200: {"model": LeaveOut, "description": "Retry of an earlier request (same key)"},
        409: {"model": ErrorOut, "description": "Overlaps an existing leave"},
    },
)
async def apply_leave(
    body: LeaveCreate,
    key: IdempotencyKey,
    session: CurrentSession,
    pool: Pool,
    response: Response,
) -> LeaveOut:
    fingerprint = request_hash(body)
    async with pool.acquire() as conn, conn.transaction():
        replay = await conn.fetchrow("SELECT * FROM hostel_leaves WHERE idempotency_key = $1", key)
        if replay is not None:
            if replay["reg_no"] != session.reg_no:
                raise HTTPException(status.HTTP_409_CONFLICT, "Idempotency-Key already used")
            if replay["request_hash"] != fingerprint:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    "Idempotency-Key reused with a different request",
                )
            response.status_code = status.HTTP_200_OK
            return leave_out(replay)

        student = await conn.fetchrow(
            "SELECT is_hosteller FROM students WHERE reg_no = $1 FOR UPDATE", session.reg_no
        )
        if not student["is_hosteller"]:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "Hostel leave is only for hostel residents"
            )
        if body.from_date < campus_today():
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "Leave cannot start in the past"
            )
        max_days = conventions().policies.hostel_leave_max_days
        if (body.to_date - body.from_date).days + 1 > max_days:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, f"Leave can be at most {max_days} days"
            )
        overlapping = await conn.fetchval(
            """
            SELECT id FROM hostel_leaves
            WHERE reg_no = $1 AND status IN ('PENDING', 'APPROVED')
              AND from_date <= $3 AND to_date >= $2
            LIMIT 1
            """,
            session.reg_no,
            body.from_date,
            body.to_date,
        )
        if overlapping is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "These dates overlap a leave you already applied for"
            )
        row = await conn.fetchrow(
            """
            INSERT INTO hostel_leaves (reg_no, from_date, to_date, reason, channel,
                                       idempotency_key, request_hash)
            VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *
            """,
            session.reg_no,
            body.from_date,
            body.to_date,
            body.reason,
            body.channel,
            key,
            fingerprint,
        )
        return leave_out(row)
