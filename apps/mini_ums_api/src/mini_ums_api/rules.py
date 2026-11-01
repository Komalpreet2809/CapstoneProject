"""Deterministic rule checks. Numbers the student hears are computed here, never by a model.

Exact fractions avoid float edge cases at the boundary (e.g. 75.0% must count as meeting a
75% threshold).
"""

import math
from dataclasses import dataclass
from datetime import date, datetime
from fractions import Fraction
from zoneinfo import ZoneInfo

CAMPUS_TZ = ZoneInfo("Asia/Kolkata")


def campus_today(now: datetime | None = None) -> date:
    return (now or datetime.now(CAMPUS_TZ)).astimezone(CAMPUS_TZ).date()


@dataclass(frozen=True)
class AttendanceSummary:
    percent: float | None
    meets_threshold: bool | None
    classes_needed: int
    can_miss: int


def attendance_summary(held: int, attended: int, threshold_percent: float) -> AttendanceSummary:
    """Percentage, threshold check, and how many classes to attend or may be missed.

    classes_needed: smallest k with (attended + k) / (held + k) >= t.
    can_miss: largest m with attended / (held + m) >= t.
    """
    if not 0 < threshold_percent < 100:
        raise ValueError("threshold must be between 0 and 100 (exclusive)")
    if held < 0 or not 0 <= attended <= held:
        raise ValueError(f"invalid attendance {attended}/{held}")
    t = Fraction(str(threshold_percent)) / 100
    if held == 0:
        return AttendanceSummary(None, None, 0, 0)
    ratio = Fraction(attended, held)
    needed = max(0, math.ceil((t * held - attended) / (1 - t)))
    can_miss = max(0, math.floor(attended / t - held))
    return AttendanceSummary(
        percent=round(float(ratio * 100), 2),
        meets_threshold=ratio >= t,
        classes_needed=needed,
        can_miss=can_miss,
    )


def password_expires_in_days(changed_on: date, today: date, max_age_days: int) -> int:
    """Negative once the password has expired."""
    return max_age_days - (today - changed_on).days
