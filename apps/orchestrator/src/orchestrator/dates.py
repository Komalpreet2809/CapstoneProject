"""Deterministic date and time parsing for what students say (brief §8: normalisers in code).

`find_day` / `find_after` pull the phrase out of a transcript (the rules classifier); the LLM
classifier returns the same phrases as heard. `resolve_day` / `resolve_after` turn a phrase into
a date or time relative to the campus clock, so "tomorrow" never depends on a model.

Conventions:
- A bare weekday ("on Friday") is the next one, today included; "next Friday" is strictly
  after today.
- A clock hour without am/pm between 1 and 7 means the afternoon: classes run 9:00-17:00, so
  "after 2" is 14:00, never 02:00.
"""

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

CAMPUS_TZ = ZoneInfo("Asia/Kolkata")
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
NOW = "now"

_DAY = re.compile(
    r"\b(day after tomorrow|tomorrow|today|tonight|yesterday|"
    r"(?:next\s+|this\s+)?(?:" + "|".join(WEEKDAYS) + r")|\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)
_AFTER = re.compile(
    r"\b(?:after|from)\s+(noon|\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)?)(?![\w:])",
    re.IGNORECASE,
)
_NEXT_CLASS = re.compile(r"\bnext\s+(class|lecture|period)\b", re.IGNORECASE)
_CLOCK = re.compile(r"^(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?$", re.IGNORECASE)


def campus_now() -> datetime:
    return datetime.now(CAMPUS_TZ)


# --- finding the phrase in a transcript --------------------------------------------------------


def find_day(text: str) -> str | None:
    match = _DAY.search(text)
    return match.group(1).lower() if match else None


def find_after(text: str) -> str | None:
    """'after 2 pm' -> '2 pm'; 'what's my next class' -> 'now'; nothing -> None."""
    if match := _AFTER.search(text):
        return match.group(1).lower()
    return NOW if _NEXT_CLASS.search(text) else None


# --- resolving it ------------------------------------------------------------------------------


def resolve_day(said: str | None, today: date) -> date:
    """Raise ValueError for a phrase that isn't a day."""
    if not said:
        return today
    phrase = re.sub(r"\s+", " ", said.strip().lower())
    if phrase.startswith("on "):
        phrase = phrase[3:]
    relative = {"today": 0, "tonight": 0, "tomorrow": 1, "day after tomorrow": 2, "yesterday": -1}
    if phrase in relative:
        return today + timedelta(days=relative[phrase])
    strictly_after = phrase.startswith("next ")
    name = phrase.removeprefix("next ").removeprefix("this ")
    if name in WEEKDAYS:
        ahead = (WEEKDAYS.index(name) - today.weekday()) % 7
        if ahead == 0 and strictly_after:
            ahead = 7
        return today + timedelta(days=ahead)
    return date.fromisoformat(phrase)


def resolve_after(said: str | None, now: datetime) -> time | None:
    """Raise ValueError for a phrase that isn't a clock time."""
    if not said:
        return None
    phrase = said.strip().lower()
    if phrase == NOW:
        return now.time().replace(second=0, microsecond=0)
    if phrase == "noon":
        return time(12)
    match = _CLOCK.match(phrase)
    if not match:
        raise ValueError(f"not a time: {said!r}")
    hour, minute = int(match.group(1)), int(match.group(2) or 0)
    meridiem = (match.group(3) or "").replace(".", "")
    if minute > 59 or hour > 23 or (meridiem and not 1 <= hour <= 12):
        raise ValueError(f"not a time: {said!r}")
    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0
    elif not meridiem and 1 <= hour <= 7:
        hour += 12
    return time(hour, minute)


# --- saying it -----------------------------------------------------------------------------------


def spoken_time(value: time) -> str:
    """14:00 -> '2 PM', 09:30 -> '9:30 AM'."""
    hour = value.hour % 12 or 12
    suffix = "AM" if value.hour < 12 else "PM"
    return f"{hour} {suffix}" if value.minute == 0 else f"{hour}:{value.minute:02d} {suffix}"


def spoken_date(value: date) -> str:
    """'Friday, 6 November'."""
    return f"{value:%A}, {value.day} {value:%B}"


def spoken_day(value: date, today: date) -> str:
    """'today', 'tomorrow', or 'on Friday, 6 November'."""
    if value == today:
        return "today"
    if value == today + timedelta(days=1):
        return "tomorrow"
    return f"on {spoken_date(value)}"
