from typing import Literal

from voiceserve_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "orchestrator"
    # Defaults suit running on the host against `make up`; Compose overrides them.
    redis_url: str = "redis://localhost:6380/0"
    mini_ums_api_url: str = "http://localhost:8001"

    # Shared secret for service-to-service calls (web -> orchestrator, gateway -> orchestrator).
    internal_api_key: str = "dev-internal-key"
    session_ttl_seconds: int = 3600

    # Intent extraction. Empty means: Anthropic when a key is configured, else the free rules
    # classifier. REPLAY_MODE overrides both with recorded outputs.
    llm_provider: Literal["", "anthropic", "rules"] = ""
    llm_model: str = "claude-haiku-5-5"
    anthropic_api_key: str = ""
