"""Mask personal data before it reaches a log line (non-negotiable rule 11).

Two layers:
- `mask_text` scrubs free text: Indian mobile numbers in common spoken/written groupings, and
  any run of 6+ digits (numeric student IDs, OTPs, unformatted phone numbers). Short numbers
  such as ticket IDs, times, dates and latencies are left alone.
- `mask_value` walks structured data: secrets are redacted outright, identifier fields keep
  only their last two characters, and every other string goes through `mask_text`.

Masks have a fixed width so they never reveal the original length. The student ID format is
generic here until `conventions.yaml` defines it (M2).
"""

import re
from collections.abc import Mapping
from typing import Any

MASK = "****"
REDACTED = "[REDACTED]"

# Optional +91 / 0091 / 91 / 0 prefix, then a 10-digit mobile starting 6-9,
# written as 10 digits, 5-5, or 3-3-4 with spaces or hyphens.
_PHONE = re.compile(
    r"(?<![\d+])(?:(?:\+|00)?91[\s-]?|0)?[6-9]\d{2}(?:\d{2}[\s-]?\d{5}|[\s-]?\d{3}[\s-]?\d{4})(?!\d)"
)
# `\d` matches any Unicode decimal digit, so Devanagari and Gurmukhi digits are covered too.
_LONG_DIGITS = re.compile(r"(?<!\d)\d{6,}(?!\d)")

SECRET_KEYS = frozenset(
    {
        "password",
        "otp",
        "otp_code",
        "code_hash",
        "token",
        "authorization",
        "cookie",
        "set_cookie",
        "secret",
        "api_key",
    }
)
SECRET_SUFFIXES = ("_token", "_secret", "_password", "_api_key")
ID_KEYS = frozenset(
    {
        "student_id",
        "phone",
        "phone_mock",
        "phone_number",
        "mobile",
        "registration_no",
        "roll_no",
    }
)


def _keep_last_two(digits: str) -> str:
    return MASK + digits[-2:]


def mask_identifier(value: str) -> str:
    return MASK + value[-2:] if len(value) > 2 else MASK


def mask_text(text: str) -> str:
    text = _PHONE.sub(lambda m: _keep_last_two(re.sub(r"\D", "", m.group())), text)
    return _LONG_DIGITS.sub(lambda m: _keep_last_two(m.group()), text)


def _normalise_key(key: str) -> str:
    return key.strip().lower().replace("-", "_")


def _is_secret(key: str) -> bool:
    return key in SECRET_KEYS or key.endswith(SECRET_SUFFIXES)


def mask_value(value: Any, key: str | None = None) -> Any:
    """Return a masked copy of `value`. `key` is the field name the value was stored under."""
    k = _normalise_key(key) if key is not None else None
    if k is not None and _is_secret(k):
        return REDACTED
    if isinstance(value, Mapping):
        return {name: mask_value(item, str(name)) for name, item in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        return [mask_value(item, key) for item in value]
    if k in ID_KEYS and value is not None:
        return mask_identifier(str(value))
    if isinstance(value, str):
        return mask_text(value)
    return value
