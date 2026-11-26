"""Navigate matching against the real Mini UMS menu catalogue."""

from functools import cache

import pytest

from mini_ums_api.conventions import conventions
from orchestrator import replies
from orchestrator.intent import RulesClassifier
from orchestrator.navigation import MenuEntry, entries_from_catalogue, match_page, words


@cache
def menu() -> tuple[MenuEntry, ...]:
    c = conventions()
    catalogue = {"menu": [m.model_dump() for m in c.menu]}
    return tuple(entries_from_catalogue(catalogue))


@pytest.mark.parametrize(
    ("said", "entry_id", "href"),
    [
        ("fee dashboard", "fee-dashboard", "/m/fee-dashboard"),
        ("Fee Dashboard", "fee-dashboard", "/m/fee-dashboard"),
        ("fees", "fee-dashboard", "/m/fee-dashboard"),  # keyword
        ("hostel leave", "hostel-leave", "/m/hostel-leave"),
        ("hostel leave application", "hostel-leave", "/m/hostel-leave"),
        ("time table", "time-table", "/m/time-table"),
        ("timetable", "time-table", "/m/time-table"),
        ("attendance", "student-attendance", "/attendance"),  # a real page
        ("exam date sheet", "exam-date-sheet", "/m/exam-date-sheet"),
        ("placement portal", "placement-drives", "/m/placement-drives"),
        ("the issued books page", "issued-books", "/m/issued-books"),
    ],
)
def test_matches(said: str, entry_id: str, href: str) -> None:
    match = match_page(said, list(menu()))
    assert match.entry is not None, said
    assert (match.entry.id, match.entry.href) == (entry_id, href)


@pytest.mark.parametrize("said", ["the weather", "pizza", "", "my page"])
def test_unknown_pages_are_not_guessed(said: str) -> None:
    assert match_page(said, list(menu())).entry is None


def test_every_entry_finds_itself_by_its_label() -> None:
    entries = list(menu())
    misses = []
    for e in entries:
        m = match_page(e.label, entries)
        if m.entry is None or m.entry.id != e.id:
            misses.append(e.label)
    assert misses == []


def test_ties_are_offered_not_guessed() -> None:
    a = MenuEntry("a", "Fee Receipts", "/m/a", "Admin › Fees")
    b = MenuEntry("b", "Hostel Receipts", "/m/b", "Admin › Hostel")
    match = match_page("receipts", [a, b])
    assert match.entry is None and match.ambiguous
    assert replies.page_ambiguous(match).text == "Did you mean Fee Receipts or Hostel Receipts?"


def test_words_drop_filler_and_plurals() -> None:
    assert words("Open the Fee Receipts page") == ["open", "fee", "receipt"]


@pytest.mark.parametrize(
    ("text", "target"),
    [
        ("open fee dashboard", "fee dashboard"),
        ("Take me to the hostel leave page", "the hostel leave"),
        ("go to RMS", "RMS"),
        ("please open my time table", "my time table"),
        ("can you open exam date sheet?", "exam date sheet"),
    ],
)
async def test_rules_navigate(text: str, target: str) -> None:
    result = await RulesClassifier().classify(text)
    assert (result.intent, result.target) == ("navigate", target)


async def test_questions_are_not_navigation() -> None:
    assert (await RulesClassifier().classify("what's my fee")).intent == "fees"
    assert (await RulesClassifier().classify("show my timetable")).intent == "timetable"


def test_navigate_reply_card() -> None:
    entry = MenuEntry("fee-dashboard", "Fee Dashboard", "/m/fee-dashboard", "Administrative › Fee")
    reply = replies.navigate(entry)
    assert reply.text == "Opening Fee Dashboard."
    assert reply.card == {
        "kind": "navigate",
        "title": "Fee Dashboard",
        "body": "Administrative › Fee",
        "href": "/m/fee-dashboard",
    }
