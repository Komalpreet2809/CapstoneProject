"""Re-seed the Mini UMS database: `python -m mini_ums_api.seed [--seed 42] [--students 600]`.

Replaces all data. Personas keep their data whatever the options. `--stats` prints the
dataset's sanity statistics without touching the database.
"""

import argparse
import asyncio
import json
from datetime import date

from mini_ums_api.db import create_pool, migrate
from mini_ums_api.seed.generate import generate, stats
from mini_ums_api.seed.load import seed_database
from mini_ums_api.settings import Settings


async def _reseed(settings: Settings, seed: int, today: date | None, students: int) -> None:
    pool = await create_pool(settings.database_url)
    try:
        await migrate(pool)
        ds = await seed_database(pool, seed, today, students)
    finally:
        await pool.close()
    counts = {table: len(rows) for table, rows in ds.tables.items()}
    print(json.dumps({"seed": seed, "today": ds.today.isoformat(), "rows": counts}, indent=2))


def main() -> None:
    settings = Settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=settings.seed)
    parser.add_argument("--students", type=int, default=settings.seed_students)
    parser.add_argument("--today", type=date.fromisoformat, default=settings.seed_today)
    parser.add_argument("--stats", action="store_true", help="print statistics only")
    args = parser.parse_args()
    if args.stats:
        ds = generate(args.seed, args.today, args.students)
        print(json.dumps({k: round(v, 3) for k, v in stats(ds).items()}, indent=2))
        return
    asyncio.run(_reseed(settings, args.seed, args.today, args.students))


if __name__ == "__main__":
    main()
