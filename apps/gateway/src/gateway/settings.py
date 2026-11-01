from voiceserve_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "gateway"
    # Defaults suit running on the host against `make up`; Compose overrides them.
    orchestrator_url: str = "http://localhost:8002"
    redis_url: str = "redis://localhost:6380/0"
    internal_api_key: str = "dev-internal-key"

    # LiveKit: the server URL services use, and the one browsers are told to connect to.
    livekit_url: str = "ws://localhost:7880"
    livekit_public_url: str = "ws://localhost:7880"
    # Placeholder pair of `livekit-server --dev`; set real keys for LiveKit Cloud.
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"
    agent_name: str = "voiceserve"

    # Speech providers (D-027). Without a key, and outside replay mode, voice is not offered.
    deepgram_api_key: str = ""
    stt_model: str = "nova-3"
    tts_voice: str = "aura-2-andromeda-en"
    # Voice turns are refused below this remaining daily budget (one turn costs ~$0.01).
    min_budget_for_voice_usd: float = 0.02

    @property
    def livekit_http_url(self) -> str:
        """LiveKit serves plain HTTP on the same port as its WebSocket (ws->http, wss->https)."""
        return self.livekit_url.replace("ws", "http", 1)

    @property
    def voice_mode(self) -> str | None:
        if self.replay_mode:
            return "replay"
        return "live" if self.deepgram_api_key else None
