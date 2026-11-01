from typing import Any

import pytest


def row(
    code: str,
    title: str,
    attended: int,
    held: int,
    *,
    threshold: float = 75.0,
) -> dict[str, Any]:
    """An attendance row shaped like the Mini UMS API's, with the API's arithmetic."""
    import math

    percent = None if held == 0 else attended / held * 100
    meets = None if percent is None else percent >= threshold
    needed = 0
    if percent is not None and not meets:
        needed = math.ceil((threshold * held - 100 * attended) / (100 - threshold))
    can_miss = 0
    if percent is not None and meets:
        can_miss = math.floor((100 * attended - threshold * held) / threshold)
    return {
        "course_code": code,
        "course_title": title,
        "held": held,
        "attended": attended,
        "percent": percent,
        "threshold": threshold,
        "meets_threshold": meets,
        "classes_needed": needed,
        "can_miss": can_miss,
        "last_updated": "2026-10-31T12:30:00Z",
    }


@pytest.fixture
def rows() -> list[dict[str, Any]]:
    return [
        row("CSE305", "Database Management Systems", 26, 30),
        row("CSE316", "Operating Systems", 30, 36),
        row("CSE326", "Computer Networks", 30, 41),
        row("CSE331", "Design and Analysis of Algorithms", 34, 37),
        row("CSE357", "Full Stack Development Lab", 10, 12),
        row("GEN231", "Professional Communication", 0, 0),
    ]
