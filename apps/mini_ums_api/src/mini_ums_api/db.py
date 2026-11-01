"""Connection pool and a minimal forward-only migration runner.

Migrations are the numbered `migrations/*.sql` files, applied in name order inside one
transaction each and recorded in `schema_migrations`. An advisory lock makes concurrent
starts (several replicas, tests) safe.
"""

from importlib.resources import files

import asyncpg

_MIGRATION_LOCK = 774_201


async def create_pool(dsn: str) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=10)
    assert pool is not None
    return pool


def _migration_files() -> list[tuple[str, str]]:
    folder = files("mini_ums_api").joinpath("migrations")
    sql = [f for f in folder.iterdir() if f.name.endswith(".sql")]
    return [(f.name, f.read_text(encoding="utf-8")) for f in sorted(sql, key=lambda f: f.name)]


async def migrate(pool: asyncpg.Pool) -> list[str]:
    """Apply pending migrations; return the names applied."""
    applied_now: list[str] = []
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute("SELECT pg_advisory_xact_lock($1)", _MIGRATION_LOCK)
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        done = {r["name"] for r in await conn.fetch("SELECT name FROM schema_migrations")}
        for name, sql in _migration_files():
            if name in done:
                continue
            await conn.execute(sql)
            await conn.execute("INSERT INTO schema_migrations (name) VALUES ($1)", name)
            applied_now.append(name)
    return applied_now
