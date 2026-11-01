"""Write a generated dataset into Postgres (replacing whatever is there) in one transaction."""

import asyncio
from datetime import date

import asyncpg

from mini_ums_api.seed.generate import Dataset, generate

# Foreign-key order. Tables not listed here are emptied but not seeded (sessions, drive_acks).
TABLE_ORDER = [
    "programmes",
    "faculty",
    "courses",
    "students",
    "enrollments",
    "attendance",
    "marks",
    "timetable",
    "fees",
    "assignments",
    "submissions",
    "exams",
    "seating",
    "tickets",
    "ticket_events",
    "hostel_leaves",
    "announcements",
    "news",
    "events",
    "messages",
    "placement_drives",
]
# Tables whose ids are referenced by other seeded rows, so the generator assigns them.
EXPLICIT_IDS = ["assignments", "exams", "placement_drives"]


async def load(pool: asyncpg.Pool, ds: Dataset) -> None:
    async with pool.acquire() as conn, conn.transaction():
        everything = [*TABLE_ORDER, "sessions", "drive_acks"]
        await conn.execute(f"TRUNCATE {', '.join(everything)} RESTART IDENTITY CASCADE")
        for table in TABLE_ORDER:
            rows = ds.rows(table)
            if not rows:
                continue
            columns = list(rows[0])
            await conn.copy_records_to_table(
                table, records=[tuple(r[c] for c in columns) for r in rows], columns=columns
            )
        for table in EXPLICIT_IDS:
            await conn.execute(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'),"
                f" (SELECT max(id) FROM {table}))"
            )
        await conn.execute("SELECT setval('ticket_seq', $1)", 1000 + len(ds.rows("tickets")))


async def is_empty(pool: asyncpg.Pool) -> bool:
    return bool(await pool.fetchval("SELECT NOT EXISTS (SELECT 1 FROM students)"))


async def seed_database(
    pool: asyncpg.Pool, seed: int, today: date | None, n_students: int
) -> Dataset:
    ds = await asyncio.to_thread(generate, seed, today, n_students)
    await load(pool, ds)
    return ds
