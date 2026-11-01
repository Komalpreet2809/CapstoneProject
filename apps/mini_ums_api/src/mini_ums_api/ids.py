"""Speakable request IDs (rule 9).

A ticket number is a 4-digit sequence plus one Damm check digit, e.g. 1001 -> "10019".
Damm catches every single-digit error and every adjacent transposition, which are the
typical mistakes when a number is heard or typed back. On screen the number sits inside the
UMS-style request ID "DEPT/Mon-YY/NNNNN"; the voice agent only ever reads the number.
"""

import re
from datetime import datetime

_DAMM = (
    (0, 3, 1, 7, 5, 9, 8, 6, 4, 2),
    (7, 0, 9, 2, 1, 5, 4, 8, 6, 3),
    (4, 2, 0, 6, 8, 7, 1, 3, 5, 9),
    (1, 7, 5, 0, 9, 8, 3, 4, 2, 6),
    (6, 1, 2, 3, 0, 4, 5, 9, 7, 8),
    (3, 6, 7, 4, 2, 0, 9, 5, 8, 1),
    (5, 8, 6, 9, 7, 2, 0, 1, 3, 4),
    (8, 9, 4, 5, 3, 6, 2, 0, 1, 7),
    (9, 4, 3, 8, 6, 1, 7, 2, 0, 5),
    (2, 5, 8, 1, 4, 3, 6, 7, 9, 0),
)

_REQUEST_ID = re.compile(
    r"^(?P<dept>[A-Z]{2,6})/(?P<month>[A-Z][a-z]{2})-(?P<yy>\d{2})/(?P<number>\d{5})$"
)


def damm_check_digit(digits: str) -> int:
    interim = 0
    for ch in digits:
        interim = _DAMM[interim][int(ch)]
    return interim


def is_valid_number(number: str) -> bool:
    return number.isascii() and number.isdigit() and damm_check_digit(number) == 0


def ticket_number(sequence: int) -> str:
    if not 1000 <= sequence <= 9999:
        raise ValueError(f"ticket sequence out of range: {sequence}")
    base = str(sequence)
    return f"{base}{damm_check_digit(base)}"


def request_id(dept: str, created_at: datetime, number: str) -> str:
    return f"{dept}/{created_at:%b}-{created_at:%y}/{number}"


def number_from_request_id(value: str) -> str | None:
    """Accept a full request ID or a bare number; return the number if it is valid."""
    value = value.strip()
    match = _REQUEST_ID.match(value)
    number = match.group("number") if match else value
    return number if is_valid_number(number) and len(number) == 5 else None


def speakable(number: str) -> str:
    """'10019' -> '1 0 0 1 9': the form the voice agent reads aloud."""
    return " ".join(number)
