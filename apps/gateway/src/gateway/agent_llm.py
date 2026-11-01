"""The orchestrator, presented to LiveKit Agents as an LLM (D-026).

LiveKit only generates a reply when the session has an LLM, so this adapter takes that place:
for each finished user turn it sends the transcript to the orchestrator's streaming turn API
and passes the reply sentences on as they arrive, so text-to-speech can start on the first
one. The card and the orchestrator's timings go to callbacks. When the user interrupts, the
stream is cancelled, which closes the HTTP request to the orchestrator (barge-in).
"""

import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from livekit.agents import APIConnectOptions, llm
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, NotGivenOr

log = logging.getLogger(__name__)

# Speaking a sentence that isn't in the tool output would break rule 5, so failures say so.
FAILURE_SENTENCE = "Sorry, I couldn't get that answer just now. Please try again."

Card = dict[str, Any]
OnCard = Callable[[Card], Awaitable[None]]
OnDone = Callable[[dict[str, Any]], None]
AllowTurn = Callable[[], Awaitable[bool]]


def latest_user_text(chat_ctx: llm.ChatContext) -> str:
    for item in reversed(chat_ctx.items):
        if isinstance(item, llm.ChatMessage) and item.role == "user":
            return item.text_content or ""
    return ""


class OrchestratorLLM(llm.LLM[Any]):
    def __init__(
        self,
        client: httpx.AsyncClient,
        session_id: str,
        *,
        on_card: OnCard,
        on_done: OnDone,
        allow_turn: AllowTurn,
    ) -> None:
        super().__init__()
        self.client = client
        self.session_id = session_id
        self.on_card = on_card
        self.on_done = on_done
        self.allow_turn = allow_turn

    @property
    def model(self) -> str:
        return "voiceserve-orchestrator"

    @property
    def provider(self) -> str:
        return "voiceserve"

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool] | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[llm.ToolChoice] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
    ) -> llm.LLMStream:
        return OrchestratorStream(
            self, chat_ctx=chat_ctx, tools=tools or [], conn_options=conn_options
        )


class OrchestratorStream(llm.LLMStream):
    _llm: OrchestratorLLM

    def _say(self, request_id: str, text: str) -> None:
        delta = llm.ChoiceDelta(role="assistant", content=text + " ")
        self._event_ch.send_nowait(llm.ChatChunk(id=request_id, delta=delta))

    async def _run(self) -> None:
        owner = self._llm
        request_id = uuid.uuid4().hex
        text = latest_user_text(self._chat_ctx).strip()
        if not text:
            return
        if not await owner.allow_turn():
            # Budget spent: no paid text-to-speech; the card explains.
            await owner.on_card(
                {
                    "kind": "message",
                    "title": "Voice paused for today",
                    "body": "The daily voice budget is used up. You can still type your question.",
                }
            )
            return
        try:
            async with owner.client.stream(
                "POST",
                f"/sessions/{owner.session_id}/turns",
                json={"text": text, "channel": "voice"},
            ) as response:
                if response.status_code != 200:
                    raise httpx.HTTPStatusError(
                        f"turn answered {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if event["type"] == "sentence":
                        self._say(request_id, event["text"])
                    elif event["type"] == "card":
                        await owner.on_card(event["card"])
                    elif event["type"] == "done":
                        owner.on_done(event)
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as exc:
            log.warning("orchestrator turn failed", extra={"error": type(exc).__name__})
            self._say(request_id, FAILURE_SENTENCE)
