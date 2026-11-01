from voiceserve_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "orchestrator"
    # Defaults suit running on the host against `make up`; Compose overrides them.
    redis_url: str = "redis://localhost:6380/0"
    mini_ums_api_url: str = "http://localhost:8001"
