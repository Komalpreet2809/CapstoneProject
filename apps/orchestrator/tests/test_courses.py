from typing import Any

import pytest

from orchestrator.courses import match_course, normalise_code, spoken_code


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("CSE326", "CSE326"),
        ("cse 326", "CSE326"),
        ("CSE-326", "CSE326"),
        ("  cse326  ", "CSE326"),
        ("gen 231", "GEN231"),
        ("computer networks", None),
        ("326", None),
        ("CSE3260", None),
    ],
)
def test_normalise_code(text: str, code: str | None) -> None:
    assert normalise_code(text) == code


def test_spoken_code_separates_letters_and_number() -> None:
    assert spoken_code("CSE326") == "CSE 326"
    assert spoken_code("weird") == "weird"


@pytest.mark.parametrize(
    ("mention", "expected"),
    [
        ("cse 326", "CSE326"),
        ("CSE-305", "CSE305"),
        ("326", "CSE326"),
        ("computer networks", "CSE326"),
        ("Computer Network", "CSE326"),  # singular/plural
        ("networks", "CSE326"),
        ("operating systems", "CSE316"),
        ("dbms", "CSE305"),  # acronym
        ("os", "CSE316"),
        ("algorithms", "CSE331"),
        ("the full stack lab", "CSE357"),
        ("professional communication", "GEN231"),
    ],
)
def test_matches_one_course(mention: str, expected: str, rows: list[dict[str, Any]]) -> None:
    match = match_course(mention, rows)
    assert match.course is not None and match.course["course_code"] == expected


@pytest.mark.parametrize("mention", ["chemistry", "CSE999", "999", "", None])
def test_no_match(mention: str | None, rows: list[dict[str, Any]]) -> None:
    match = match_course(mention, rows)
    assert match.course is None and not match.ambiguous


def test_equally_good_matches_are_ambiguous(rows: list[dict[str, Any]]) -> None:
    # "systems" is in two titles equally
    match = match_course("systems", rows)
    assert match.course is None and match.ambiguous
    assert {c["course_code"] for c in match.candidates} == {"CSE305", "CSE316"}
