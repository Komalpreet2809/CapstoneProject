"""Provider prices in USD, used to estimate and record spend against the daily budget (D-028).

Checked against the providers' public pricing pages on 2026-11-01. Update the date and the
numbers together when re-verifying. Replay mode costs nothing.
"""

from dataclasses import dataclass

PRICES_CHECKED_ON = "2026-11-01"


@dataclass(frozen=True)
class TokenPrice:
    input_per_mtok: float
    output_per_mtok: float


# Anthropic Messages API, first-party rates (prompts up to 100K tokens for Haiku 5.5).
LLM_PRICES: dict[str, TokenPrice] = {
    "claude-haiku-5-5": TokenPrice(0.10, 0.50),
    "claude-sonnet-5-5": TokenPrice(2.00, 10.00),
    "claude-opus-5-5": TokenPrice(4.00, 20.00),
}

# Deepgram pay-as-you-go: Nova-3 monolingual streaming STT, Aura-2 TTS.
STT_USD_PER_MINUTE = 0.0077
TTS_USD_PER_1K_CHARS = 0.030


def llm_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    # An unknown model is priced like the most expensive known one, never as free.
    price = LLM_PRICES.get(model) or max(LLM_PRICES.values(), key=lambda p: p.output_per_mtok)
    return (input_tokens * price.input_per_mtok + output_tokens * price.output_per_mtok) / 1e6


def stt_cost(audio_seconds: float) -> float:
    return audio_seconds / 60 * STT_USD_PER_MINUTE


def tts_cost(characters: int) -> float:
    return characters / 1000 * TTS_USD_PER_1K_CHARS
