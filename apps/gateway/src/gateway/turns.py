"""Per-turn latency for voice (brief: "latency logged"; target first audio p50 < 1.0 s).

LiveKit Agents reports metrics per reply, keyed by speech id: end of utterance (VAD/turn
end -> turn committed, including the final transcript), LLM time to first token (here, the
orchestrator's first sentence) and TTS time to first byte. Time to first audio is their sum,
measured from the moment the student stopped speaking.
"""

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Turn:
    eou_s: float | None = None
    transcription_s: float | None = None
    ttft_s: float | None = None
    ttfb_s: float | None = None
    agent: dict[str, Any] = field(default_factory=dict)


def _ms(seconds: float | None) -> int | None:
    return None if seconds is None else round(seconds * 1000)


class TurnLatency:
    def __init__(self, channel: str = "voice") -> None:
        self._channel = channel
        self._turns: dict[str, _Turn] = {}
        self._agent_timings: list[dict[str, Any]] = []

    def eou(self, speech_id: str, end_of_utterance: float, transcription: float) -> None:
        turn = self._turns.setdefault(speech_id, _Turn())
        turn.eou_s, turn.transcription_s = end_of_utterance, transcription

    def llm(self, speech_id: str, ttft: float) -> None:
        turn = self._turns.setdefault(speech_id, _Turn())
        if turn.ttft_s is None:
            turn.ttft_s = ttft
            if self._agent_timings:
                turn.agent = self._agent_timings.pop(0)

    def agent_done(self, timings: dict[str, Any]) -> None:
        self._agent_timings.append(timings)

    def tts(self, speech_id: str, ttfb: float) -> dict[str, Any] | None:
        """The first audio of a reply completes its record, which is returned once."""
        turn = self._turns.get(speech_id)
        if turn is None or turn.ttfb_s is not None or ttfb < 0:
            return None
        turn.ttfb_s = ttfb
        parts = (turn.eou_s, turn.ttft_s, turn.ttfb_s)
        first_audio = sum(p for p in parts if p is not None) if turn.eou_s is not None else None
        record = {
            "channel": self._channel,
            "speech_id": speech_id,
            "end_of_utterance_ms": _ms(turn.eou_s),
            "transcription_ms": _ms(turn.transcription_s),
            "agent_first_sentence_ms": _ms(turn.ttft_s),
            "tts_first_audio_ms": _ms(turn.ttfb_s),
            "first_audio_ms": _ms(first_audio),
            "agent_total_ms": turn.agent.get("agent_total_ms"),
            "at": time.time(),
        }
        del self._turns[speech_id]
        return {k: v for k, v in record.items() if v is not None}
