"""Spoken replies and on-screen cards, built from tool output by code (D-029).

Every number spoken or shown comes from the Mini UMS API's attendance rows: counts as given,
percentages rounded to whole numbers. The LLM never writes a reply in M3, so numbers are
grounded by construction (rule 4). Sentences are short so text-to-speech can start on the
first one while the rest are still being sent.
"""

from dataclasses import dataclass, field
from datetime import date, time
from typing import Any

from orchestrator.courses import CourseMatch, spoken_code
from orchestrator.dates import spoken_day, spoken_time

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
        "Ask me about your attendance, fees, timetable, exams or assignments.",
    ]
    return Reply(s, _message("VoiceServe", " ".join(s)))


def help_reply() -> Reply:
    s = [
        "I can tell you your attendance, fee dues, timetable, exams and seating, "
        "and pending assignments.",
        "Requests and hostel leave are coming soon.",
    ]
    return Reply(s, _message("What I can do", " ".join(s)))


def unsupported(feature: str | None) -> Reply:
    what = feature or "that"
    s = [
        f"I can't help with {what} by voice yet.",
        "I can tell you your attendance, fees, timetable, exams or assignments.",
    ]
    return Reply(s, _message("Not available yet", " ".join(s)))


def out_of_scope() -> Reply:
    s = [
        "Sorry, I can only help with your student portal.",
        "Try asking about your attendance, fees or timetable.",
    ]
    return Reply(s, _message("Outside what I can do", " ".join(s)))


def session_ended() -> Reply:
    s = ["Your portal session has ended.", "Please log in again to continue."]
    return Reply(s, _message("Session ended", " ".join(s), {"href": "/login", "label": "Log in"}))


def data_unavailable(what: str = "attendance records", link: dict[str, str] | None = None) -> Reply:
    # Rule 5: say so, never guess.
    s = [f"I couldn't reach your {what} just now.", "Please try again in a moment."]
    return Reply(s, _message(f"Couldn't load {what}", " ".join(s), link or ATTENDANCE_LINK))


# --- fees, timetable, exams, assignments ------------------------------------------------------
# Every amount, date, time and count is read from the API response; code only counts rows and
# formats them (rule 4).

FEES_LINK = {"href": "/m/fee-dashboard", "label": "Open fee dashboard"}
TIMETABLE_LINK = {"href": "/m/time-table", "label": "Open time table"}
EXAMS_LINK = {"href": "/m/exam-date-sheet", "label": "Open date sheet"}
ASSIGNMENTS_LINK = {"href": "/m/pending-assignments", "label": "Open assignments"}
SPOKEN_LIMIT = 4  # beyond this, rows go on the card only


def unclear_day() -> Reply:
    s = [
        "Sorry, I didn't catch which day or time you meant.",
        "Try today, tomorrow, a weekday, or a time like after 2 PM.",
    ]
    return Reply(s, _message("Which day?", " ".join(s), TIMETABLE_LINK))


def rupees(amount: float) -> str:
    """Indian digit grouping: 120000 -> '1,20,000'; paise only when present."""
    whole, paise = divmod(round(amount * 100), 100)
    digits = str(whole)
    head, tail = digits[:-3], digits[-3:]
    groups: list[str] = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    text = ",".join([g for g in (head, *groups) if g] + [tail])
    return f"{text}.{paise:02d}" if paise else text


def _plural(n: int, word: str, many: str | None = None) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {many or word + 's'}"


def _short_date(value: date) -> str:
    return f"{value.day} {value:%b}"


def _list(
    title: str, summary: str, items: list[dict[str, Any]], link: dict[str, str]
) -> dict[str, Any]:
    return {"kind": "list", "title": title, "summary": summary, "items": items, "link": link}


def _item(label: str, value: str, note: str = "", status: str = "none") -> dict[str, Any]:
    return {"label": label, "value": value, "note": note, "status": status}


def _fee_item(i: dict[str, Any]) -> dict[str, Any]:
    on = _short_date(date.fromisoformat(i["due_date"]))
    if i["due"] <= 0:
        return _item(i["head"], "Paid", f"₹{rupees(i['amount'])} paid in full", "ok")
    note = f"Overdue since {on}" if i["overdue"] else f"Due {on}"
    return _item(i["head"], f"₹{rupees(i['due'])}", note, "low" if i["overdue"] else "warn")


def fee_for_head(data: dict[str, Any], head: str, today: date) -> Reply:
    """One kind of fee ('hostel', 'examination', ...), across its instalments."""
    items = sorted(
        (i for i in data["items"] if head in i["head"].lower()), key=lambda i: i["due_date"]
    )
    label = f"{head.capitalize()} fee"
    if not items:
        s = [f"I couldn't find a {head} fee on your account.", "Here are all your fees."]
        reply = fees(data, today)
        return Reply(s + reply.sentences, reply.card)
    s = []
    for i in items:
        if i["due"] <= 0:
            s.append(f"Your {i['head']} of {rupees(i['amount'])} rupees is fully paid.")
            continue
        when = spoken_day(date.fromisoformat(i["due_date"]), today)
        if i["overdue"]:
            s.append(
                f"Your {i['head']} has {rupees(i['due'])} rupees pending, overdue since {when}."
            )
        else:
            s.append(f"Your {i['head']} has {rupees(i['due'])} rupees pending, due {when}.")
    summary = s[0]
    return Reply(s, _list(label, summary, [_fee_item(i) for i in items], FEES_LINK))


def fees(data: dict[str, Any], today: date, head: str | None = None) -> Reply:
    if head:
        return fee_for_head(data, head, today)
    due = sorted((i for i in data["items"] if i["due"] > 0), key=lambda i: i["due_date"])
    if not due:
        s = ["You have no fees due right now.", "Your fee status is NIL."]
        return Reply(s, _list("Fees", s[0], [], FEES_LINK))
    s = [f"You have {rupees(data['total_due'])} rupees due in total."]
    if data["overdue_due"] > 0:
        s.append(f"{rupees(data['overdue_due'])} rupees of that is overdue.")
    upcoming = [i for i in due if not i["overdue"]]
    if upcoming:
        when = spoken_day(date.fromisoformat(upcoming[0]["due_date"]), today)
        s.append(f"The next payment, {upcoming[0]['head']}, is due {when}.")
    return Reply(s, _list("Fees", s[0], [_fee_item(i) for i in due], FEES_LINK))


def _class_words(e: dict[str, Any]) -> str:
    start = spoken_time(time.fromisoformat(e["start"]))
    mandatory = ", mandatory" if e["mandatory"] else ""
    name = f"{spoken_code(e['course_code'])}, {e['course_title']}"
    return f"{name}, at {start} in room {e['room']}{mandatory}"


def timetable(data: dict[str, Any], today: date, after: time | None, next_only: bool) -> Reply:
    day = date.fromisoformat(data["date"])
    when = spoken_day(day, today)
    entries = data["entries"][:1] if next_only else data["entries"]
    after_words = f" after {spoken_time(after)}" if after and not next_only else ""
    if next_only:
        s = (
            [f"Your next class is {_class_words(entries[0])}."]
            if entries
            else [f"You have no more classes {when}."]
        )
    elif not entries:
        s = [f"You have no classes {when}{after_words}."]
    else:
        s = [f"You have {_plural(len(entries), 'class', 'classes')} {when}{after_words}."]
        s += [f"{_class_words(e)}." for e in entries[:SPOKEN_LIMIT]]
        if len(entries) > SPOKEN_LIMIT:
            s.append(f"And {len(entries) - SPOKEN_LIMIT} more on screen.")
    items = [
        _item(
            f"{e['start'][:5]}-{e['end'][:5]}",
            e["course_code"],
            " · ".join(
                [e["course_title"], e["room"], e["kind"]]
                + (["Mandatory"] if e["mandatory"] else [])
            ),
            "warn" if e["mandatory"] else "none",
        )
        for e in entries
    ]
    title = f"Time table · {data['weekday']} {_short_date(day)}"
    return Reply(s, _list(title, s[0], items, TIMETABLE_LINK))


def exams(rows: list[dict[str, Any]], today: date) -> Reply:
    upcoming = sorted(
        (r for r in rows if date.fromisoformat(r["date"]) >= today),
        key=lambda r: (r["date"], r["start"]),
    )
    if not upcoming:
        s = ["You have no upcoming exams."]
        return Reply(s, _list("Upcoming exams", s[0], [], EXAMS_LINK))
    first = upcoming[0]
    when = spoken_day(date.fromisoformat(first["date"]), today)
    start = spoken_time(time.fromisoformat(first["start"]))
    s = [
        f"Your next exam is {spoken_code(first['course_code'])}, {first['course_title']}, "
        f"{first['exam_type']}, {when} at {start}."
    ]
    seat = first["seating"]
    if seat:
        s.append(f"Your seat is {seat['seat']} in room {seat['room']}, {seat['building']}.")
    else:
        s.append("Your seat hasn't been allotted yet.")
    if len(upcoming) > 1:
        s.append(f"You have {_plural(len(upcoming) - 1, 'more exam')} after that, on screen.")
    items = []
    for r in upcoming:
        seat_note = (
            [f"Seat {r['seating']['seat']}, room {r['seating']['room']}"] if r["seating"] else []
        )
        items.append(
            _item(
                f"{_short_date(date.fromisoformat(r['date']))} {r['start'][:5]}",
                r["course_code"],
                " · ".join([r["course_title"], r["exam_type"], *seat_note]),
            )
        )
    return Reply(s, _list("Upcoming exams", s[0], items, EXAMS_LINK))


def assignments(rows: list[dict[str, Any]], today: date) -> Reply:
    pending = sorted(rows, key=lambda r: (r["last_date"], r["id"]))
    if not pending:
        s = ["You have no pending assignments."]
        return Reply(s, _list("Pending assignments", s[0], [], ASSIGNMENTS_LINK))
    first = pending[0]
    when = spoken_day(date.fromisoformat(first["last_date"]), today)
    s = [
        f"You have {_plural(len(pending), 'pending assignment')}.",
        f"The next one is {first['title']} for {spoken_code(first['course_code'])}, "
        f"{first['course_title']}, due {when}.",
    ]
    items = []
    for r in pending:
        left = r["days_left"]
        status = "low" if left <= 1 else "warn" if left <= 3 else "ok"
        left_words = "due today" if left == 0 else f"{_plural(left, 'day')} left"
        due_on = _short_date(date.fromisoformat(r["last_date"]))
        items.append(
            _item(
                r["course_code"],
                r["title"],
                f"{r['course_title']} · Due {due_on} · {left_words}",
                status,
            )
        )
    return Reply(s, _list("Pending assignments", s[0], items, ASSIGNMENTS_LINK))
