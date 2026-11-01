"""RMS: log requests, see history, add notes, give feedback after closure.

Safety rules enforced here, not in any prompt:
- rule 3: `Idempotency-Key` is required; a retry returns the original ticket.
- rule 7: a similar open ticket (same category and sub-category) is returned as 409 so the
  caller can offer a note on it instead; `allow_duplicate` overrides after the user chooses.
- rule 9: ticket numbers carry a check digit (ids.py).
- rule 10: the current declaration version must be sent (validated in TicketCreate).
"""

from typing import Annotated

import asyncpg
from fastapi import APIRouter, HTTPException, Path, Response, status
from fastapi.responses import JSONResponse

from mini_ums_api.conventions import conventions
from mini_ums_api.deps import CurrentSession, IdempotencyKey, Pool, request_hash
from mini_ums_api.ids import is_valid_number, request_id, speakable, ticket_number
from mini_ums_api.rules import CAMPUS_TZ
from mini_ums_api.schemas import (
    DuplicateTicketOut,
    ErrorOut,
    Feedback,
    FeedbackIn,
    NoteIn,
    TicketCounts,
    TicketCreate,
    TicketDetailOut,
    TicketEventOut,
    TicketHistoryOut,
    TicketOut,
)

router = APIRouter(prefix="/me/tickets", tags=["rms"])

OPEN_STATES = ["OPEN", "IN_PROGRESS", "REOPENED"]
TicketNumber = Annotated[
    str, Path(pattern=r"^[0-9]{5}$", description="5-digit ticket number, e.g. 10019")
]


def ticket_out(r: asyncpg.Record) -> TicketOut:
    category = conventions().rms.category(r["category"])
    feedback = (
        Feedback(
            resolved=r["feedback_resolved"],
            rating=r["feedback_rating"],
            comment=r["feedback_comment"],
            at=r["feedback_at"],
        )
        if r["feedback_at"] is not None
        else None
    )
    return TicketOut(
        number=r["number"],
        request_id=request_id(r["dept"], r["created_at"].astimezone(CAMPUS_TZ), r["number"]),
        speakable=speakable(r["number"]),
        dept=r["dept"],
        category=r["category"],
        category_label=category.label if category else r["category"],
        sub_category=r["sub_category"],
        block=r["block"],
        room=r["room"],
        title=r["title"],
        description=r["description"],
        status=r["status"],
        priority=r["priority"],
        channel=r["channel"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        closing_remarks=r["closing_remarks"],
        closed_at=r["closed_at"],
        feedback=feedback,
        can_give_feedback=r["status"] == "CLOSED" and r["feedback_at"] is None,
    )


async def _owned(
    conn: asyncpg.Connection, reg_no: str, number: str, lock: bool = False
) -> asyncpg.Record:
    # A ticket that isn't yours is reported as missing, so numbers can't be probed.
    if not is_valid_number(number):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    row = await conn.fetchrow(
        "SELECT * FROM tickets WHERE number = $1 AND reg_no = $2" + (" FOR UPDATE" if lock else ""),
        number,
        reg_no,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    return row


async def _detail(conn: asyncpg.Connection, ticket: asyncpg.Record) -> TicketDetailOut:
    events = await conn.fetch(
        "SELECT status_from, status_to, note, actor, at FROM ticket_events"
        " WHERE ticket_number = $1 ORDER BY at, id",
        ticket["number"],
    )
    return TicketDetailOut(
        **ticket_out(ticket).model_dump(), events=[TicketEventOut(**dict(e)) for e in events]
    )


@router.get("", response_model=TicketHistoryOut)
async def history(session: CurrentSession, pool: Pool) -> TicketHistoryOut:
    rows = await pool.fetch(
        "SELECT * FROM tickets WHERE reg_no = $1 ORDER BY created_at DESC, number DESC",
        session.reg_no,
    )
    tickets = [ticket_out(r) for r in rows]
    open_count = sum(t.status in OPEN_STATES for t in tickets)
    return TicketHistoryOut(
        counts=TicketCounts(total=len(tickets), open=open_count, closed=len(tickets) - open_count),
        tickets=tickets,
    )


@router.get("/latest", response_model=TicketDetailOut, responses={404: {"model": ErrorOut}})
async def latest(session: CurrentSession, pool: Pool) -> TicketDetailOut:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tickets WHERE reg_no = $1 ORDER BY created_at DESC, number DESC LIMIT 1",
            session.reg_no,
        )
        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "You have no requests yet")
        return await _detail(conn, row)


@router.get("/{number}", response_model=TicketDetailOut, responses={404: {"model": ErrorOut}})
async def get_ticket(number: TicketNumber, session: CurrentSession, pool: Pool) -> TicketDetailOut:
    async with pool.acquire() as conn:
        return await _detail(conn, await _owned(conn, session.reg_no, number))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketOut,
    responses={
        200: {"model": TicketOut, "description": "Retry of an earlier request (same key)"},
        409: {"model": DuplicateTicketOut, "description": "Similar open request exists"},
        422: {"description": "Invalid request, or key reused with a different request"},
    },
)
async def create_ticket(
    body: TicketCreate,
    key: IdempotencyKey,
    session: CurrentSession,
    pool: Pool,
    response: Response,
) -> TicketOut | JSONResponse:
    fingerprint = request_hash(body)
    category = conventions().rms.category(body.category)
    assert category is not None  # validated by TicketCreate
    async with pool.acquire() as conn:
        replay = await conn.fetchrow("SELECT * FROM tickets WHERE idempotency_key = $1", key)
        if replay is None and not body.allow_duplicate:
            similar = await conn.fetchrow(
                """
                SELECT * FROM tickets
                WHERE reg_no = $1 AND category = $2 AND sub_category = $3 AND status = ANY ($4)
                ORDER BY created_at DESC LIMIT 1
                """,
                session.reg_no,
                body.category,
                body.sub_category,
                OPEN_STATES,
            )
            if similar is not None:
                duplicate = DuplicateTicketOut(
                    detail="You already have an open request like this one",
                    similar=ticket_out(similar),
                )
                return JSONResponse(status_code=409, content=duplicate.model_dump(mode="json"))
        if replay is None:
            try:
                async with conn.transaction():
                    number = ticket_number(await conn.fetchval("SELECT nextval('ticket_seq')"))
                    await conn.execute(
                        """
                        INSERT INTO tickets (number, dept, reg_no, category, sub_category, block,
                            room, title, description, channel, declaration_version,
                            idempotency_key, request_hash)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        """,
                        number,
                        category.dept,
                        session.reg_no,
                        body.category,
                        body.sub_category,
                        body.block if category.needs_location else None,
                        body.room if category.needs_location else None,
                        body.title,
                        body.description,
                        body.channel,
                        body.declaration_version,
                        key,
                        fingerprint,
                    )
                    await conn.execute(
                        "INSERT INTO ticket_events (ticket_number, status_to, note, actor)"
                        " VALUES ($1, 'OPEN', $2, 'student')",
                        number,
                        f"Request logged via {body.channel}",
                    )
                    return ticket_out(
                        await conn.fetchrow("SELECT * FROM tickets WHERE number = $1", number)
                    )
            except asyncpg.UniqueViolationError:
                # A concurrent retry with the same key won the race; return its ticket.
                replay = await conn.fetchrow(
                    "SELECT * FROM tickets WHERE idempotency_key = $1", key
                )
                if replay is None:
                    raise
    if replay["reg_no"] != session.reg_no:
        raise HTTPException(status.HTTP_409_CONFLICT, "Idempotency-Key already used")
    if replay["request_hash"] != fingerprint:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Idempotency-Key reused with a different request"
        )
    response.status_code = status.HTTP_200_OK
    return ticket_out(replay)


@router.post(
    "/{number}/notes",
    response_model=TicketDetailOut,
    responses={404: {"model": ErrorOut}, 409: {"model": ErrorOut}},
)
async def add_note(
    number: TicketNumber, body: NoteIn, session: CurrentSession, pool: Pool
) -> TicketDetailOut:
    async with pool.acquire() as conn, conn.transaction():
        ticket = await _owned(conn, session.reg_no, number, lock=True)
        if ticket["status"] == "CLOSED":
            raise HTTPException(
                status.HTTP_409_CONFLICT, "This request is closed; reopen it through feedback"
            )
        await conn.execute(
            "INSERT INTO ticket_events (ticket_number, status_from, status_to, note, actor)"
            " VALUES ($1, $2, $2, $3, 'student')",
            number,
            ticket["status"],
            body.note,
        )
        ticket = await conn.fetchrow(
            "UPDATE tickets SET updated_at = now() WHERE number = $1 RETURNING *", number
        )
        return await _detail(conn, ticket)


@router.post(
    "/{number}/feedback",
    response_model=TicketDetailOut,
    responses={404: {"model": ErrorOut}, 409: {"model": ErrorOut}},
)
async def give_feedback(
    number: TicketNumber, body: FeedbackIn, session: CurrentSession, pool: Pool
) -> TicketDetailOut:
    """After closure: 'resolved' keeps it closed; 'not resolved' reopens it."""
    async with pool.acquire() as conn, conn.transaction():
        ticket = await _owned(conn, session.reg_no, number, lock=True)
        if ticket["status"] != "CLOSED" or ticket["feedback_at"] is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Feedback can be given once, after the request is closed"
            )
        new_status = "CLOSED" if body.resolved else "REOPENED"
        ticket = await conn.fetchrow(
            """
            UPDATE tickets
            SET feedback_resolved = $2, feedback_rating = $3, feedback_comment = $4,
                feedback_at = now(), status = $5, updated_at = now()
            WHERE number = $1 RETURNING *
            """,
            number,
            body.resolved,
            body.rating,
            body.comment,
            new_status,
        )
        default_note = "Marked resolved" if body.resolved else "Not resolved; request reopened"
        await conn.execute(
            "INSERT INTO ticket_events (ticket_number, status_from, status_to, note, actor)"
            " VALUES ($1, 'CLOSED', $2, $3, 'student')",
            number,
            new_status,
            body.comment or default_note,
        )
        return await _detail(conn, ticket)
