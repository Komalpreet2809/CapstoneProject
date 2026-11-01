"""Speech providers for REPLAY_MODE (D-028): free, offline and deterministic.

`ReplaySTT` hears each spoken segment (VAD decides where segments end) and returns the next
recorded transcript from `replay_transcripts.json`, in order. A scripted test speaks into
Chrome's fake microphone and knows exactly what the agent will "hear".

`ReplayTTS` stands in for speech with a soft tone as long as the sentence would take to say,
so playback, interruption and latency are exercised without a provider.
"""

import itertools
import json
import math
import struct
import uuid
from importlib.resources import files
from typing import Any

from livekit.agents import APIConnectOptions, LanguageCode, stt, tts
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, NotGivenOr
from livekit.agents.utils import AudioBuffer

SAMPLE_RATE = 24_000
SECONDS_PER_CHAR = 0.045
MAX_SECONDS = 8.0


def load_transcripts() -> list[str]:
    raw = files("gateway").joinpath("replay_transcripts.json").read_text("utf-8")
    transcripts: list[str] = json.loads(raw)
    return transcripts


class ReplaySTT(stt.STT[Any]):
    def __init__(self, transcripts: list[str]) -> None:
        super().__init__(capabilities=stt.STTCapabilities(streaming=False, interim_results=False))
        self._next = itertools.cycle(transcripts)

    @property
    def model(self) -> str:
        return "replay"

    @property
    def provider(self) -> str:
        return "replay"

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[
                stt.SpeechData(language=LanguageCode("en"), text=next(self._next), confidence=1.0)
            ],
        )


def tone(seconds: float, sample_rate: int = SAMPLE_RATE) -> bytes:
    """16-bit mono PCM: a quiet 330 Hz tone with short fades, so it never clicks."""
    count = int(seconds * sample_rate)
    fade = min(count // 2, int(0.02 * sample_rate))
    out = bytearray()
    for i in range(count):
        envelope = min(1.0, i / fade, (count - 1 - i) / fade) if fade else 1.0
        sample = int(2500 * envelope * math.sin(2 * math.pi * 330 * i / sample_rate))
        out += struct.pack("<h", sample)
    return bytes(out)


class ReplayTTS(tts.TTS[Any]):
    def __init__(self) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=SAMPLE_RATE,
            num_channels=1,
        )

    @property
    def model(self) -> str:
        return "replay"

    @property
    def provider(self) -> str:
        return "replay"

    def synthesize(
        self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    ) -> tts.ChunkedStream:
        return _ToneStream(tts=self, input_text=text, conn_options=conn_options)


class _ToneStream(tts.ChunkedStream):
    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        output_emitter.initialize(
            request_id=uuid.uuid4().hex,
            sample_rate=SAMPLE_RATE,
            num_channels=1,
            mime_type="audio/pcm",
        )
        seconds = min(MAX_SECONDS, max(0.3, len(self.input_text) * SECONDS_PER_CHAR))
        output_emitter.push(tone(seconds))
        output_emitter.flush()
