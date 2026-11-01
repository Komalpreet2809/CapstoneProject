from voiceserve_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "gateway"
    # Defaults suit running on the host against `make up`; Compose overrides them.
    orchestrator_url: str = "http://localhost:8002"
    livekit_url: str = "ws://localhost:7880"

    @property
    def livekit_http_url(self) -> str:
        """LiveKit serves plain HTTP on the same port as its WebSocket (ws->http, wss->https)."""
        return self.livekit_url.replace("ws", "http", 1)
