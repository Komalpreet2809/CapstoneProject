from datetime import date, datetime, time

import pytest

from orchestrator.dates import (
    CAMPUS_TZ,
    find_after,
    find_day,
    resolve_after,
    resolve_day,
    spoken_day,
    spoken_time,
)

TODAY = date(2026, 11, 5)  # a Thursday
NOW = datetime(2026, 11, 5, 13, 42, tzinfo=CAMPUS_TZ)


@pytest.mark.parametrize(
    ("text", "day"),
    [
        ("what classes do I have today", "today"),
        ("timetable for tomorrow", "tomorrow"),
        ("classes day after tomorrow", "day after tomorrow"),
        ("what do I have on Friday", "friday"),
        ("timetable next Monday", "next monday"),
        ("schedule for 2026-11-09", "2026-11-09"),
        ("what's my timetable", None),
    ],
)
def test_find_day(text: str, day: str | None) -> None:
    assert find_day(text) == day


@pytest.mark.parametrize(
    ("text", "after"),
    [
        ("classes after 2 pm", "2 pm"),
        ("any lectures after 2", "2"),
        ("mandatory classes after 14:30 today", "14:30"),
        ("classes from 11 a.m.", "11 a.m."),
        ("anything after noon", "noon"),
        ("what's my next class", "now"),
        ("what's my timetable", None),
        ("after the exam", None),
    ],
)
def test_find_after(text: str, after: str | None) -> None:
    assert find_after(text) == after


@pytest.mark.parametrize(
    ("said", "expected"),
    [
        (None, date(2026, 11, 5)),
        ("today", date(2026, 11, 5)),
        ("Tomorrow", date(2026, 11, 6)),
        ("day after tomorrow", date(2026, 11, 7)),
        ("yesterday", date(2026, 11, 4)),
        ("thursday", date(2026, 11, 5)),  # bare weekday: today counts
        ("next thursday", date(2026, 11, 12)),  # "next": strictly after today
        ("on friday", date(2026, 11, 6)),
        ("monday", date(2026, 11, 9)),
        ("next monday", date(2026, 11, 9)),
        ("2026-12-01", date(2026, 12, 1)),
    ],
)
def test_resolve_day(said: str | None, expected: date) -> None:
    assert resolve_day(said, TODAY) == expected


@pytest.mark.parametrize("said", ["someday", "the 5th", "2026-13-01"])
def test_resolve_day_rejects(said: str) -> None:
    with pytest.raises(ValueError):
        resolve_day(said, TODAY)


@pytest.mark.parametrize(
    ("said", "expected"),
    [
        (None, None),
        ("2 pm", time(14)),
        ("2", time(14)),  # 1-7 without am/pm = afternoon
        ("9", time(9)),
        ("11 a.m.", time(11)),
        ("12 pm", time(12)),
        ("12 am", time(0)),
        ("14:30", time(14, 30)),
        ("2:15pm", time(14, 15)),
        ("noon", time(12)),
        ("now", time(13, 42)),
    ],
)
def test_resolve_after(said: str | None, expected: time | None) -> None:
    assert resolve_after(said, NOW) == expected


@pytest.mark.parametrize("said", ["13 pm", "25", "2:75", "soon"])
def test_resolve_after_rejects(said: str) -> None:
    with pytest.raises(ValueError):
        resolve_after(said, NOW)


@pytest.mark.parametrize(
    ("value", "spoken"), [(time(14), "2 PM"), (time(9, 30), "9:30 AM"), (time(12), "12 PM")]
)
def test_spoken_time(value: time, spoken: str) -> None:
    assert spoken_time(value) == spoken


def test_spoken_day() -> None:
    assert spoken_day(TODAY, TODAY) == "today"
    assert spoken_day(date(2026, 11, 6), TODAY) == "tomorrow"
    assert spoken_day(date(2026, 11, 9), TODAY) == "on Monday, 9 November"
