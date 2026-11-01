"""Spoken replies and on-screen cards, built from tool output by code (D-029).

Every number spoken or shown comes from the Mini UMS API's attendance rows: counts as given,
percentages rounded to whole numbers. The LLM never writes a reply in M3, so numbers are
grounded by construction (rule 4). Sentences are short so text-to-speech can start on the
first one while the rest are still being sent.
"""

from dataclasses import dataclass, field
from typing import Any

from orchestrator.courses import CourseMatch, spoken_code

ATTENDANCE_LINK = {"href": "/attendance", "label": "Open attendance"}


@dataclass
class Reply:
    sentences: list[str]
    card: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return " ".join(self.sentences)


def _classes(n: int) -> str:
    return f"{n} class" if n == 1 else f"{n} classes"


def _pct(row: dict[str, Any]) -> int | None:
    return None if row["percent"] is None else round(row["percent"])


def _status(row: dict[str, Any]) -> str:
    pct = row["percent"]
    if pct is None:
        return "none"
    if not row["meets_threshold"]:
        return "low"
    return "warn" if pct < row["threshold"] + 5 else "ok"


def _hint(row: dict[str, Any]) -> str:
    if row["percent"] is None:
        return "No classes held yet"
    if not row["meets_threshold"]:
        return (
            f"Attend the next {_classes(row['classes_needed'])} to reach {round(row['threshold'])}%"
        )
    n = row["can_miss"]
    return "Don't miss the next class" if n == 0 else f"Can miss {_classes(n)}"


def _card_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": row["course_code"],
        "title": row["course_title"],
        "attended": row["attended"],
        "held": row["held"],
        "percent": _pct(row),
        "status": _status(row),
        "hint": _hint(row),
    }


def _card(rows: list[dict[str, Any]], summary: str, highlight: str | None = None) -> dict[str, Any]:
    return {
        "kind": "attendance",
        "title": "Attendance",
        "summary": summary,
        "rows": [_card_row(r) for r in rows],
        "highlight": highlight,
        "link": ATTENDANCE_LINK,
    }


def _name(row: dict[str, Any]) -> str:
    return f"{spoken_code(row['course_code'])}, {row['course_title']}"


def course_attendance(row: dict[str, Any]) -> Reply:
    threshold = round(row["threshold"])
    if row["percent"] is None:
        sentences = [
            f"No classes have been held yet in {_name(row)}, so there's no attendance yet."
        ]
    else:
        sentences = [
            f"In {_name(row)}, you've attended {row['attended']} of {row['held']} classes.",
            f"That's {_pct(row)} percent.",
        ]
        if not row["meets_threshold"]:
            sentences.append(
                f"That's below the {threshold} percent minimum. "
                f"Attend the next {_classes(row['classes_needed'])} in a row to reach it."
            )
        elif row["can_miss"] == 0:
            sentences.append(
                f"You're just at the {threshold} percent minimum, so don't miss the next class."
            )
        else:
            sentences.append(
                f"You can miss up to {_classes(row['can_miss']).replace(' class', ' more class')} "
                f"and stay above {threshold} percent."
            )
    return Reply(sentences, _card([row], sentences[0], highlight=row["course_code"]))


def overall_attendance(rows: list[dict[str, Any]]) -> Reply:
    if not rows:
        return Reply(
            ["You don't have any registered courses this term, so there's no attendance yet."],
            {"kind": "message", "title": "Attendance", "body": "No registered courses this term."},
        )
    held = [r for r in rows if r["percent"] is not None]
    low = [r for r in held if not r["meets_threshold"]]
    threshold = round(rows[0]["threshold"])
    sentences: list[str] = []
    if not low:
        sentences.append(
            f"You're at or above {threshold} percent in all {len(held)} "
            "of your courses with classes so far."
        )
        tightest = min(held, key=lambda r: r["can_miss"], default=None)
        if tightest is not None:
            sentences.append(f"The closest is {_name(tightest)} at {_pct(tightest)} percent.")
    else:
        sentences.append(
            f"You're below {threshold} percent in {len(low)} of your {len(held)} "
            "courses with classes so far."
        )
        for row in sorted(low, key=lambda r: r["percent"]):
            sentences.append(
                f"{_name(row)} is at {_pct(row)} percent; "
                f"attend the next {_classes(row['classes_needed'])} to reach {threshold}."
            )
    return Reply(
        sentences, _card(rows, sentences[0], highlight=low[0]["course_code"] if low else None)
    )


def course_not_found(mention: str, rows: list[dict[str, Any]]) -> Reply:
    sentence = f'I couldn\'t find a course matching "{mention}" in your registered courses.'
    return Reply(
        [sentence, "Here are the courses I can see."],
        _card(rows, sentence),
    )


def course_ambiguous(match: CourseMatch) -> Reply:
    options = " or ".join(_name(c) for c in match.candidates[:3])
    sentence = f"Did you mean {options}?"
    return Reply([sentence], _card(match.candidates, sentence))


# --- non-attendance replies ------------------------------------------------------------------


def _message(title: str, body: str, link: dict[str, str] | None = None) -> dict[str, Any]:
    card: dict[str, Any] = {"kind": "message", "title": title, "body": body}
    if link:
        card["link"] = link
    return card


def greeting(first_name: str) -> Reply:
    s = [
        f"Hi {first_name}!",
        "Ask me about your attendance, for example: am I short in any course?",
    ]
    return Reply(s, _message("VoiceServe", " ".join(s)))


def help_reply() -> Reply:
    s = [
        "Right now I can tell you your attendance, overall or for one course.",
        "Timetable, fees, exams, assignments and requests are coming soon.",
    ]
    return Reply(s, _message("What I can do", " ".join(s)))


def unsupported(feature: str | None) -> Reply:
    what = feature or "that"
    s = [f"I can't check {what} by voice yet.", "For now I can tell you your attendance."]
    return Reply(s, _message("Not available yet", " ".join(s)))


def out_of_scope() -> Reply:
    s = [
        "Sorry, I can only help with your student portal.",
        "Try asking about your attendance.",
    ]
    return Reply(s, _message("Outside what I can do", " ".join(s)))


def session_ended() -> Reply:
    s = ["Your portal session has ended.", "Please log in again to continue."]
    return Reply(s, _message("Session ended", " ".join(s), {"href": "/login", "label": "Log in"}))


def data_unavailable() -> Reply:
    # Rule 5: say so, never guess.
    s = ["I couldn't reach your attendance records just now.", "Please try again in a moment."]
    return Reply(s, _message("Couldn't load attendance", " ".join(s), ATTENDANCE_LINK))
