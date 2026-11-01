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

    # List the demo personas (with their password) for the login page. Unset: only in dev.
    # A public demo sets it explicitly; the data is synthetic either way.
    demo_accounts: bool | None = None

    @property
    def show_demo_accounts(self) -> bool:
        return self.environment == "dev" if self.demo_accounts is None else self.demo_accounts
