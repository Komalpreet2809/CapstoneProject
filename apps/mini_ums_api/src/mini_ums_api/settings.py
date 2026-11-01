from datetime import date

from voiceserve_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "mini_ums_api"
    # Defaults suit running on the host against `make up`; Compose overrides them.
    database_url: str = "postgresql://voiceserve:voiceserve@localhost:5433/voiceserve"

    # Synthetic data: generated on startup when the database is empty.
    seed_on_empty: bool = True
    seed: int = 42
    seed_students: int = 600
    seed_today: date | None = None  # anchor day for relative dates; defaults to today
