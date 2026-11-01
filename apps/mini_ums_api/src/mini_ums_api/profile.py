"""Loading a student's profile row and shaping it for the API."""

import asyncpg

from mini_ums_api.conventions import conventions
from mini_ums_api.rules import CAMPUS_TZ, campus_today, password_expires_in_days
from mini_ums_api.schemas import StudentProfile

PROFILE_SQL = """
SELECT s.reg_no, s.vid, s.name, s.programme_code, p.name AS programme, p.school, s.section,
       s.term, s.cgpa, s.is_hosteller, s.hostel_block, s.room, s.preferred_language,
       s.password_hash, s.password_changed_at, s.failed_logins, s.locked_until
FROM students s JOIN programmes p ON p.code = s.programme_code
WHERE s.reg_no = $1
"""


def profile_from_row(row: asyncpg.Record) -> StudentProfile:
    changed_on = row["password_changed_at"].astimezone(CAMPUS_TZ).date()
    return StudentProfile(
        reg_no=row["reg_no"],
        vid=row["vid"],
        name=row["name"],
        programme_code=row["programme_code"],
        programme=row["programme"],
        school=row["school"],
        section=row["section"],
        term=row["term"],
        cgpa=float(row["cgpa"]) if row["cgpa"] is not None else None,
        is_hosteller=row["is_hosteller"],
        hostel_block=row["hostel_block"],
        room=row["room"],
        preferred_language=row["preferred_language"],
        password_expires_in_days=password_expires_in_days(
            changed_on, campus_today(), conventions().policies.password_max_age_days
        ),
    )
