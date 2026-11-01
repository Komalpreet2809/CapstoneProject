"""The signed-in student's own data. Every route takes the student from the session (rule 1)."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated, Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from mini_ums_api.conventions import conventions
from mini_ums_api.deps import CurrentSession, Pool, current_session
from mini_ums_api.profile import PROFILE_SQL, profile_from_row
from mini_ums_api.rules import attendance_summary, campus_today
from mini_ums_api.schemas import (
    AssignmentOut,
    AttendanceOut,
    CourseOut,
    DriveAckIn,
    ExamOut,
    FeeItem,
    FeesOut,
    MessageOut,
    PlacementDriveOut,
    Seat,
    StudentProfile,
    TimetableEntry,
    TimetableOut,
)

router = APIRouter(prefix="/me", tags=["student"], dependencies=[Depends(current_session)])

_ATTENDANCE_SQL = """
SELECT e.course_code, c.title, c.credits, c.kind, e.term, f.name AS faculty, e.roll_no,
       e.group_no, a.held, a.attended, a.last_updated
FROM enrollments e
JOIN students s ON s.reg_no = e.reg_no AND s.term = e.term
JOIN courses c ON c.code = e.course_code
JOIN faculty f ON f.id = e.faculty_id
JOIN attendance a
  ON a.reg_no = e.reg_no AND a.course_code = e.course_code AND a.term = e.term
WHERE e.reg_no = $1
ORDER BY e.course_code
"""


def _attendance(r: asyncpg.Record) -> AttendanceOut:
    threshold = conventions().policies.attendance_min_percent
    summary = attendance_summary(r["held"], r["attended"], threshold)
    return AttendanceOut(
        course_code=r["course_code"],
        course_title=r["title"],
        held=r["held"],
        attended=r["attended"],
        percent=summary.percent,
        threshold=threshold,
        meets_threshold=summary.meets_threshold,
        classes_needed=summary.classes_needed,
        can_miss=summary.can_miss,
        last_updated=r["last_updated"],
    )


@router.get("", response_model=StudentProfile)
async def profile(session: CurrentSession, pool: Pool) -> StudentProfile:
    row = await pool.fetchrow(PROFILE_SQL, session.reg_no)
    if row is None:  # session outlived the student (re-seed)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")
    return profile_from_row(row)


@router.get("/courses", response_model=list[CourseOut])
async def courses(session: CurrentSession, pool: Pool) -> list[CourseOut]:
    rows = await pool.fetch(_ATTENDANCE_SQL, session.reg_no)
    return [
        CourseOut(
            code=r["course_code"],
            title=r["title"],
            credits=r["credits"],
            kind=r["kind"],
            term=r["term"],
            faculty=r["faculty"],
            roll_no=r["roll_no"],
            group_no=r["group_no"],
            attendance=_attendance(r),
        )
        for r in rows
    ]


@router.get("/attendance", response_model=list[AttendanceOut])
async def attendance(
    session: CurrentSession,
    pool: Pool,
    course: Annotated[str | None, Query(description="Course code, e.g. CSE326")] = None,
) -> list[AttendanceOut]:
    rows = await pool.fetch(_ATTENDANCE_SQL, session.reg_no)
    items = [_attendance(r) for r in rows]
    if course is not None:
        items = [a for a in items if a.course_code == course.strip().upper()]
    return items


@router.get("/timetable", response_model=TimetableOut)
async def timetable(
    session: CurrentSession,
    pool: Pool,
    on: Annotated[date | None, Query(alias="date", description="Defaults to today")] = None,
    after: Annotated[time | None, Query(description="Only classes starting at/after")] = None,
) -> TimetableOut:
    day = on or campus_today()
    rows = await pool.fetch(
        """
        SELECT t.start_time, t.end_time, t.course_code, c.title, t.room, t.kind, t.mandatory
        FROM students s
        JOIN timetable t ON t.section = s.section AND t.day_of_week = $2
        JOIN courses c ON c.code = t.course_code
        WHERE s.reg_no = $1 AND ($3::time IS NULL OR t.start_time >= $3::time)
        ORDER BY t.start_time
        """,
        session.reg_no,
        day.isoweekday(),
        after,
    )
    return TimetableOut(
        date=day,
        weekday=day.strftime("%A"),
        entries=[
            TimetableEntry(
                start=r["start_time"],
                end=r["end_time"],
                course_code=r["course_code"],
                course_title=r["title"],
                room=r["room"],
                kind=r["kind"],
                mandatory=r["mandatory"],
            )
            for r in rows
        ],
    )


@router.get("/fees", response_model=FeesOut)
async def fees(session: CurrentSession, pool: Pool) -> FeesOut:
    today = campus_today()
    rows = await pool.fetch(
        "SELECT head, amount, paid, due_date FROM fees WHERE reg_no = $1 ORDER BY due_date, head",
        session.reg_no,
    )
    items = []
    for r in rows:
        due = r["amount"] - r["paid"]
        items.append(
            FeeItem(
                head=r["head"],
                amount=float(r["amount"]),
                paid=float(r["paid"]),
                due=float(due),
                due_date=r["due_date"],
                overdue=due > 0 and r["due_date"] < today,
            )
        )
    return FeesOut(
        items=items,
        total_due=round(sum(i.due for i in items), 2),
        overdue_due=round(sum(i.due for i in items if i.overdue), 2),
    )


@router.get("/exams", response_model=list[ExamOut])
async def exams(session: CurrentSession, pool: Pool) -> list[ExamOut]:
    rows = await pool.fetch(
        """
        SELECT x.course_code, c.title, x.exam_type, x.exam_date, x.start_time, x.end_time,
               st.building, st.room, st.seat
        FROM enrollments e
        JOIN students s ON s.reg_no = e.reg_no AND s.term = e.term
        JOIN exams x ON x.course_code = e.course_code AND x.term = e.term
        JOIN courses c ON c.code = x.course_code
        LEFT JOIN seating st ON st.exam_id = x.id AND st.reg_no = e.reg_no
        WHERE e.reg_no = $1
        ORDER BY x.exam_date, x.start_time
        """,
        session.reg_no,
    )
    return [
        ExamOut(
            course_code=r["course_code"],
            course_title=r["title"],
            exam_type=r["exam_type"],
            date=r["exam_date"],
            start=r["start_time"],
            end=r["end_time"],
            seating=(
                Seat(building=r["building"], room=r["room"], seat=r["seat"])
                if r["seat"] is not None
                else None
            ),
        )
        for r in rows
    ]


@router.get("/assignments", response_model=list[AssignmentOut])
async def assignments(
    session: CurrentSession,
    pool: Pool,
    state: Annotated[Literal["pending", "all"], Query(alias="status")] = "pending",
) -> list[AssignmentOut]:
    today = campus_today()
    rows = await pool.fetch(
        """
        SELECT a.id, a.course_code, c.title AS course_title, a.title, a.kind, a.last_date,
               a.max_marks, sub.submitted_at
        FROM students s
        JOIN enrollments e ON e.reg_no = s.reg_no AND e.term = s.term
        JOIN assignments a ON a.section = s.section AND a.term = e.term
                          AND a.course_code = e.course_code
        JOIN courses c ON c.code = a.course_code
        LEFT JOIN submissions sub ON sub.assignment_id = a.id AND sub.reg_no = s.reg_no
        WHERE s.reg_no = $1
        ORDER BY a.last_date, a.id
        """,
        session.reg_no,
    )
    items = [
        AssignmentOut(
            id=r["id"],
            course_code=r["course_code"],
            course_title=r["course_title"],
            title=r["title"],
            kind=r["kind"],
            last_date=r["last_date"],
            max_marks=r["max_marks"],
            submitted=r["submitted_at"] is not None,
            submitted_at=r["submitted_at"],
            days_left=(r["last_date"] - today).days,
        )
        for r in rows
    ]
    if state == "pending":
        items = [a for a in items if not a.submitted and a.days_left >= 0]
    return items


@router.get("/messages", response_model=list[MessageOut])
async def messages(
    session: CurrentSession, pool: Pool, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[MessageOut]:
    rows = await pool.fetch(
        """
        SELECT m.id, m.sender_name, m.sender_role, m.subject, m.body, m.sent_at
        FROM messages m JOIN students s ON s.section = m.section
        WHERE s.reg_no = $1 ORDER BY m.sent_at DESC LIMIT $2
        """,
        session.reg_no,
        limit,
    )
    return [MessageOut(**dict(r)) for r in rows]


_ELIGIBLE_DRIVES_SQL = """
SELECT d.id, d.company, d.role, d.package_lpa, d.drive_date, d.register_by,
       ack.read_at, ack.remind_after
FROM students s
JOIN placement_drives d ON s.programme_code = ANY (d.programmes) AND s.cgpa >= d.min_cgpa
LEFT JOIN drive_acks ack ON ack.drive_id = d.id AND ack.reg_no = s.reg_no
WHERE s.reg_no = $1 AND d.register_by >= $2
ORDER BY d.register_by, d.id
"""


@router.get("/placement-drives", response_model=list[PlacementDriveOut])
async def placement_drives(
    session: CurrentSession,
    pool: Pool,
    pending_only: Annotated[
        bool, Query(description="Only unread drives that are not snoozed (login pop-up)")
    ] = False,
) -> list[PlacementDriveOut]:
    now = datetime.now(UTC)
    rows = await pool.fetch(_ELIGIBLE_DRIVES_SQL, session.reg_no, campus_today())
    drives = []
    for r in rows:
        read = r["read_at"] is not None
        snoozed = r["remind_after"] is not None and r["remind_after"] > now
        if pending_only and (read or snoozed):
            continue
        drives.append(
            PlacementDriveOut(
                id=r["id"],
                company=r["company"],
                role=r["role"],
                package_lpa=float(r["package_lpa"]),
                drive_date=r["drive_date"],
                register_by=r["register_by"],
                read=read,
            )
        )
    return drives


@router.post("/placement-drives/ack", status_code=status.HTTP_204_NO_CONTENT)
async def acknowledge_drives(body: DriveAckIn, session: CurrentSession, pool: Pool) -> None:
    eligible = {
        r["id"] for r in await pool.fetch(_ELIGIBLE_DRIVES_SQL, session.reg_no, campus_today())
    }
    unknown = set(body.drive_ids) - eligible
    if unknown:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown drives: {sorted(unknown)}")
    now = datetime.now(UTC)
    if body.action == "read":
        read_at, remind_after = now, None
    else:
        hours = conventions().policies.placement_remind_later_hours
        read_at, remind_after = None, now + timedelta(hours=hours)
    await pool.executemany(
        """
        INSERT INTO drive_acks (reg_no, drive_id, read_at, remind_after) VALUES ($1, $2, $3, $4)
        ON CONFLICT (reg_no, drive_id) DO UPDATE
        SET read_at = COALESCE(drive_acks.read_at, EXCLUDED.read_at),
            remind_after = EXCLUDED.remind_after
        """,
        [(session.reg_no, d, read_at, remind_after) for d in body.drive_ids],
    )
