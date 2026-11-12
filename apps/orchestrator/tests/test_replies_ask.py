"""Fee, timetable, exam and assignment replies: every number comes from the API rows."""

import re
from datetime import date, time
from typing import Any

import pytest

from orchestrator import replies

TODAY = date(2026, 11, 5)  # Thursday


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d[\d,]*", text))


@pytest.mark.parametrize(
    ("amount", "text"),
    [(0, "0"), (500, "500"), (3500, "3,500"), (23500, "23,500"), (120000, "1,20,000"),
     (12345678, "1,23,45,678"), (2500.5, "2,500.50")],
)  # fmt: skip
def test_rupees_indian_grouping(amount: float, text: str) -> None:
    assert replies.rupees(amount) == text


def fee(head: str, due: float, due_date: str, overdue: bool) -> dict[str, Any]:
    return {"head": head, "amount": due, "paid": 0, "due": due, "due_date": due_date,
            "overdue": overdue}  # fmt: skip


def test_fees_nil() -> None:
    reply = replies.fees({"items": [], "total_due": 0, "overdue_due": 0}, TODAY)
    assert "NIL" in reply.text
    assert reply.card["kind"] == "list" and reply.card["items"] == []


def test_fees_due_and_overdue() -> None:
    data = {
        "items": [
            fee("Tuition Fee", 30000, "2026-09-20", True),
            fee("Examination Fee", 3500, "2026-11-25", False),
            fee("Library", 0, "2026-09-20", False),
        ],
        "total_due": 33500,
        "overdue_due": 30000,
    }
    reply = replies.fees(data, TODAY)
    assert reply.sentences[0] == "You have 33,500 rupees due in total."
    assert "30,000 rupees of that is overdue." in reply.sentences
    assert "Examination Fee, is due on Wednesday, 25 November" in reply.text
    assert [i["label"] for i in reply.card["items"]] == ["Tuition Fee", "Examination Fee"]
    assert reply.card["items"][0]["status"] == "low"


def entry(start: str, code: str, mandatory: bool = False) -> dict[str, Any]:
    end = f"{int(start[:2]) + 1:02d}:00:00"
    return {"start": start, "end": end, "course_code": code, "course_title": f"Title {code}",
            "room": "B3-204", "kind": "Lecture", "mandatory": mandatory}  # fmt: skip


def day_data(entries: list[dict[str, Any]], on: str = "2026-11-06") -> dict[str, Any]:
    return {"date": on, "weekday": date.fromisoformat(on).strftime("%A"), "entries": entries}


def test_timetable_lists_classes() -> None:
    data = day_data([entry("09:00:00", "CSE326"), entry("14:00:00", "CSE357", mandatory=True)])
    reply = replies.timetable(data, TODAY, None, next_only=False)
    assert reply.sentences[0] == "You have 2 classes tomorrow."
    assert "at 9 AM in room B3-204" in reply.sentences[1]
    assert reply.sentences[2].endswith("mandatory.")
    assert reply.card["items"][1]["status"] == "warn"


def test_timetable_after_and_empty() -> None:
    reply = replies.timetable(day_data([], "2026-11-08"), TODAY, time(14), next_only=False)
    assert reply.text == "You have no classes on Sunday, 8 November after 2 PM."


def test_timetable_next_class() -> None:
    data = day_data([entry("15:00:00", "CSE316"), entry("16:00:00", "CSE305")], "2026-11-05")
    reply = replies.timetable(data, TODAY, time(13, 40), next_only=True)
    assert reply.text.startswith("Your next class is CSE 316")
    assert len(reply.card["items"]) == 1
    none = replies.timetable(day_data([], "2026-11-05"), TODAY, time(18), next_only=True)
    assert none.text == "You have no more classes today."


def test_timetable_long_day_is_capped_when_spoken() -> None:
    data = day_data([entry(f"{h:02d}:00:00", f"CSE{300 + h}") for h in (9, 10, 11, 12, 14, 15)])
    reply = replies.timetable(data, TODAY, None, next_only=False)
    assert reply.sentences[-1] == "And 2 more on screen."
    assert len(reply.card["items"]) == 6


def exam(on: str, code: str, seat: bool = True) -> dict[str, Any]:
    return {"course_code": code, "course_title": f"Title {code}", "exam_type": "End-term",
            "date": on, "start": "09:30:00", "end": "12:30:00",
            "seating": {"building": "Academic Block C", "room": "C-204", "seat": "R2-S3"}
            if seat else None}  # fmt: skip


def test_exams_next_with_seat() -> None:
    rows = [
        exam("2026-10-01", "CSE305"),
        exam("2026-11-25", "CSE326"),
        exam("2026-11-27", "CSE316"),
    ]
    reply = replies.exams(rows, TODAY)
    assert reply.sentences[0] == (
        "Your next exam is CSE 326, Title CSE326, End-term, on Wednesday, 25 November at 9:30 AM."
    )
    assert reply.sentences[1] == "Your seat is R2-S3 in room C-204, Academic Block C."
    assert reply.sentences[2] == "You have 1 more exam after that, on screen."
    assert len(reply.card["items"]) == 2  # the past paper is left out


def test_exams_none_and_no_seat() -> None:
    assert replies.exams([], TODAY).text == "You have no upcoming exams."
    reply = replies.exams([exam("2026-11-25", "CSE326", seat=False)], TODAY)
    assert "hasn't been allotted" in reply.text


def assignment(i: int, last: str, left: int) -> dict[str, Any]:
    return {"id": i, "course_code": "CSE326", "course_title": "Computer Networks",
            "title": f"Quiz {i}", "kind": "Quiz", "last_date": last, "max_marks": 10,
            "submitted": False, "submitted_at": None, "days_left": left}  # fmt: skip


def test_assignments() -> None:
    assert replies.assignments([], TODAY).text == "You have no pending assignments."
    reply = replies.assignments(
        [assignment(2, "2026-11-12", 7), assignment(1, "2026-11-05", 0)], TODAY
    )
    assert reply.sentences[0] == "You have 2 pending assignments."
    assert reply.sentences[1] == "The next one is Quiz 1 for CSE 326, Computer Networks, due today."
    assert reply.card["items"][0]["status"] == "low"
    assert "due today" in reply.card["items"][0]["note"]


def test_spoken_numbers_all_come_from_the_rows() -> None:
    """Rule 4: no number in a fee reply that isn't in the API data (amounts or dates)."""
    data = {
        "items": [fee("Hostel Fee", 20000, "2026-11-15", False)],
        "total_due": 20000,
        "overdue_due": 0,
    }
    reply = replies.fees(data, TODAY)
    allowed = {"20,000", "15"}
    assert numbers(reply.text) <= allowed
