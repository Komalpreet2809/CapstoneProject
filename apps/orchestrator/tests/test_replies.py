import re
from typing import Any

from orchestrator import replies
from orchestrator.courses import match_course


def _numbers(text: str) -> set[int]:
    return {int(n) for n in re.findall(r"\d+", text)}


def _grounded(text: str, rows: list[dict[str, Any]]) -> set[int]:
    """Numbers a reply may contain: values in the tool output (rule 4), percentages rounded."""
    allowed: set[int] = set()
    for r in rows:
        allowed |= {
            r["attended"],
            r["held"],
            r["classes_needed"],
            r["can_miss"],
            round(r["threshold"]),
        }
        allowed |= _numbers(r["course_code"])
        if r["percent"] is not None:
            allowed.add(round(r["percent"]))
    return _numbers(text) - allowed


def test_course_below_the_minimum(rows: list[dict[str, Any]]) -> None:
    reply = replies.course_attendance(rows[2])  # CSE326, 30/41
    assert reply.sentences[0] == "In CSE 326, Computer Networks, you've attended 30 of 41 classes."
    assert reply.sentences[1] == "That's 73 percent."
    assert "Attend the next 3 classes in a row" in reply.sentences[2]
    assert not _grounded(reply.text, rows)
    assert reply.card["highlight"] == "CSE326"
    assert reply.card["rows"][0]["status"] == "low"


def test_course_above_the_minimum(rows: list[dict[str, Any]]) -> None:
    reply = replies.course_attendance(rows[0])  # CSE305, 26/30
    assert "87 percent" in reply.text
    assert "You can miss up to 4 more classes" in reply.text
    assert not _grounded(reply.text, rows)


def test_course_without_classes(rows: list[dict[str, Any]]) -> None:
    reply = replies.course_attendance(rows[5])
    assert "No classes have been held yet" in reply.text
    assert reply.card["rows"][0]["percent"] is None


def test_overall_lists_every_course_below_the_minimum(rows: list[dict[str, Any]]) -> None:
    reply = replies.overall_attendance(rows)
    assert (
        reply.sentences[0] == "You're below 75 percent in 1 of your 5 courses with classes so far."
    )
    assert "CSE 326, Computer Networks is at 73 percent" in reply.sentences[1]
    assert len(reply.card["rows"]) == 6
    assert not _grounded(reply.text, rows) - {1, 5}  # counts of courses, from the row list


def test_overall_when_everything_is_fine(rows: list[dict[str, Any]]) -> None:
    fine = [r for r in rows if r["meets_threshold"] is not False]
    reply = replies.overall_attendance(fine)
    assert reply.sentences[0].startswith("You're at or above 75 percent in all 4")
    assert reply.card["highlight"] is None


def test_ambiguous_course_asks(rows: list[dict[str, Any]]) -> None:
    reply = replies.course_ambiguous(match_course("systems", rows))
    assert reply.sentences == [
        "Did you mean CSE 305, Database Management Systems or CSE 316, Operating Systems?"
    ]


def test_unknown_course_says_so(rows: list[dict[str, Any]]) -> None:
    reply = replies.course_not_found("chemistry", rows)
    assert 'couldn\'t find a course matching "chemistry"' in reply.text
    assert len(reply.card["rows"]) == len(rows)


def test_missing_data_is_never_guessed() -> None:
    reply = replies.data_unavailable()
    assert "couldn't reach" in reply.text
    assert not _numbers(reply.text)
