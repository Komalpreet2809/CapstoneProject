from voiceserve_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "mini_ums_api"
    # Defaults suit running on the host against `make up`; Compose overrides them.
    database_url: str = "postgresql://voiceserve:voiceserve@localhost:5433/voiceserve"
