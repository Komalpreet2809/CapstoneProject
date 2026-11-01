import json
from typing import Any

import httpx
from livekit.agents import llm

from gateway.agent_llm import FAILURE_SENTENCE, OrchestratorLLM
from gateway.replay import SAMPLE_RATE, tone
from gateway.turns import TurnLatency


def test_first_audio_is_the_sum_of_the_stages() -> None:
    turns = TurnLatency()
    turns.agent_done({"agent_total_ms": 42})
    turns.eou("s1", end_of_utterance=0.55, transcription=0.21)
    turns.llm("s1", ttft=0.04)
    record = turns.tts("s1", ttfb=0.31)
    assert record is not None
    assert record["first_audio_ms"] == 900
    assert record["end_of_utterance_ms"] == 550
    assert record["transcription_ms"] == 210
    assert record["agent_first_sentence_ms"] == 40
    assert record["tts_first_audio_ms"] == 310
    assert record["agent_total_ms"] == 42
    # one record per reply: later sentences of the same reply don't add another
    assert turns.tts("s1", ttfb=0.2) is None


def test_a_reply_without_a_user_turn_has_no_first_audio() -> None:
    turns = TurnLatency()
    turns.llm("s2", ttft=0.05)
    record = turns.tts("s2", ttfb=0.3)
    assert record is not None and "first_audio_ms" not in record


def test_replay_tone_is_pcm_of_the_requested_length() -> None:
    audio = tone(0.5)
    assert len(audio) == int(0.5 * SAMPLE_RATE) * 2  # 16-bit mono
    assert audio[:2] == b"\x00\x00"  # fades in from silence


def _orchestrator(events: list[dict[str, Any]] | None, status: int = 200) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content) == {"text": "am I short?", "channel": "voice"}
        if events is None:
            raise httpx.ConnectError("down", request=request)
        body = "".join(json.dumps(e) + "\n" for e in events)
        return httpx.Response(status, content=body.encode())

    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://orch")


async def _run(
    client: httpx.AsyncClient, *, allow: bool = True
) -> tuple[str, list[Any], list[Any]]:
    cards: list[Any] = []
    done: list[Any] = []

    async def on_card(card: dict[str, Any]) -> None:
        cards.append(card)

    async def allow_turn() -> bool:
        return allow

    adapter = OrchestratorLLM(
        client, "sess", on_card=on_card, on_done=done.append, allow_turn=allow_turn
    )
    ctx = llm.ChatContext()
    ctx.add_message(role="user", content="am I short?")
    text = ""
    async with adapter.chat(chat_ctx=ctx) as stream:
        async for chunk in stream:
            if chunk.delta and chunk.delta.content:
                text += chunk.delta.content
    return text.strip(), cards, done


async def test_sentences_stream_in_order_and_the_card_is_forwarded() -> None:
    events = [
        {"type": "sentence", "text": "You're below 75 percent in 1 course."},
        {"type": "sentence", "text": "Attend the next 3 classes."},
        {"type": "card", "card": {"kind": "attendance"}},
        {"type": "done", "timings": {"agent_total_ms": 12}},
    ]
    text, cards, done = await _run(_orchestrator(events))
    assert text == "You're below 75 percent in 1 course. Attend the next 3 classes."
    assert cards == [{"kind": "attendance"}]
    assert done[0]["timings"] == {"agent_total_ms": 12}


async def test_an_unreachable_orchestrator_is_admitted_not_guessed() -> None:
    text, cards, _ = await _run(_orchestrator(None))
    assert text == FAILURE_SENTENCE
    assert cards == []


async def test_no_speech_when_the_budget_is_spent() -> None:
    text, cards, _ = await _run(_orchestrator([]), allow=False)
    assert text == ""
    assert cards[0]["title"] == "Voice paused for today"
