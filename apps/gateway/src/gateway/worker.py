"""The realtime voice pipeline: a LiveKit Agents worker (brief §6.3, D-026).

Per voice session it joins room `vs-<session id>` and runs: Silero VAD + end of turn ->
streaming STT (Deepgram, or replay) -> the orchestrator (as the "LLM") -> sentence-level TTS
(Deepgram, or replay). Push-to-talk is three RPCs from the widget: `start_turn` (mic on, and
interrupt any speech: barge-in), `end_turn`, `cancel_turn`. The mic stays on while the agent
speaks so the student can also interrupt by talking; it goes off when the agent finishes.

Run with `python -m gateway.worker start` (`dev` reloads on change).
"""

import asyncio
import json
import logging
from typing import Any

import httpx
import redis.asyncio as aioredis
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    AgentStateChangedEvent,
    JobContext,
    MetricsCollectedEvent,
    TurnHandlingOptions,
    cli,
    metrics,
    room_io,
)
from livekit.agents import stt as lk_stt
from livekit.plugins import deepgram, silero

from gateway.agent_llm import OrchestratorLLM
from gateway.replay import ReplaySTT, ReplayTTS, load_transcripts
from gateway.settings import Settings
from gateway.turns import TurnLatency
from voiceserve_common import latency
from voiceserve_common.budget import BudgetGuard
from voiceserve_common.pricing import stt_cost, tts_cost

log = logging.getLogger("voiceserve.worker")
settings = Settings()
server = AgentServer(
    ws_url=settings.livekit_url,
    api_key=settings.livekit_api_key,
    api_secret=settings.livekit_api_secret,
    num_idle_processes=2,  # the production default (20) is far more than a laptop needs
)


class VoiceAgent(Agent):
    """Instructions stay empty: the orchestrator owns the conversation, not a prompt here."""

    def __init__(self) -> None:
        super().__init__(instructions="")


def _speech(replay: bool, vad: Any) -> tuple[Any, Any]:
    if replay:
        return lk_stt.StreamAdapter(stt=ReplaySTT(load_transcripts()), vad=vad), ReplayTTS()
    return (
        deepgram.STT(model=settings.stt_model, api_key=settings.deepgram_api_key),
        deepgram.TTS(model=settings.tts_voice, api_key=settings.deepgram_api_key),
    )


@server.rtc_session(agent_name=settings.agent_name)
async def entrypoint(ctx: JobContext) -> None:
    session_id = json.loads(ctx.job.metadata or "{}").get("session_id", "")
    replay = settings.replay_mode
    redis = aioredis.from_url(settings.redis_url)
    guard = BudgetGuard(redis, settings.daily_budget_usd)
    client = httpx.AsyncClient(
        base_url=settings.orchestrator_url,
        headers={"X-Internal-Key": settings.internal_api_key},
        timeout=httpx.Timeout(15.0, connect=3.0),
    )

    async def close_clients() -> None:
        await client.aclose()
        await redis.aclose()

    ctx.add_shutdown_callback(close_clients)

    if (await client.get(f"/sessions/{session_id}")).status_code != 200:
        log.warning("dispatch for an unknown or expired voice session; leaving")
        return

    await ctx.connect()
    vad = silero.VAD.load()
    stt_provider, tts_provider = _speech(replay, vad)
    turns = TurnLatency()
    user_turn_open = False
    tasks: set[asyncio.Task[Any]] = set()

    def background(coro: Any) -> None:
        task = asyncio.create_task(coro)
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    async def send_card(card: dict[str, Any]) -> None:
        await ctx.room.local_participant.publish_data(
            json.dumps(card).encode(), reliable=True, topic="voiceserve.card"
        )

    async def allow_turn() -> bool:
        return replay or await guard.remaining() >= settings.min_budget_for_voice_usd

    session: AgentSession[None] = AgentSession(
        stt=stt_provider,
        vad=vad,
        llm=OrchestratorLLM(
            client,
            session_id,
            on_card=send_card,
            on_done=lambda event: turns.agent_done(event.get("timings", {})),
            allow_turn=allow_turn,
        ),
        tts=tts_provider,
        turn_handling=TurnHandlingOptions(
            turn_detection="vad",
            interruption={"enabled": True, "min_duration": 0.3},
        ),
    )

    @session.on("metrics_collected")
    def on_metrics(event: MetricsCollectedEvent) -> None:
        m = event.metrics
        if isinstance(m, metrics.EOUMetrics) and m.speech_id:
            turns.eou(m.speech_id, m.end_of_utterance_delay, m.transcription_delay)
        elif isinstance(m, metrics.LLMMetrics) and m.speech_id:
            turns.llm(m.speech_id, m.ttft)
        elif isinstance(m, metrics.TTSMetrics):
            if not replay:
                background(guard.record(tts_cost(m.characters_count)))
            if m.speech_id and (record := turns.tts(m.speech_id, m.ttfb)):
                log.info("voice turn latency %s", json.dumps(record))
                background(latency.record(redis, record))
        elif isinstance(m, metrics.STTMetrics) and not replay:
            background(guard.record(stt_cost(m.audio_duration)))

    @session.on("agent_state_changed")
    def on_agent_state(event: AgentStateChangedEvent) -> None:
        # Mic input is only taken while the student talks or could interrupt a reply.
        if event.old_state == "speaking" and event.new_state != "speaking" and not user_turn_open:
            session.input.set_audio_enabled(False)

    await session.start(
        agent=VoiceAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(close_on_disconnect=True),
    )
    session.input.set_audio_enabled(False)

    participant = ctx.room.local_participant

    async def start_turn(data: rtc.RpcInvocationData) -> str:
        nonlocal user_turn_open
        user_turn_open = True
        session.interrupt()  # barge-in: stop speaking and cancel the reply in progress
        session.clear_user_turn()
        session.input.set_audio_enabled(True)
        return "listening"

    async def end_turn(data: rtc.RpcInvocationData) -> str:
        nonlocal user_turn_open
        user_turn_open = False
        session.commit_user_turn()  # audio stays on until the reply ends, for barge-in
        return "committed"

    async def cancel_turn(data: rtc.RpcInvocationData) -> str:
        nonlocal user_turn_open
        user_turn_open = False
        session.input.set_audio_enabled(False)
        session.clear_user_turn()
        return "cancelled"

    for handler in (start_turn, end_turn, cancel_turn):
        participant.register_rpc_method(handler.__name__, handler)


if __name__ == "__main__":
    cli.run_app(server)
