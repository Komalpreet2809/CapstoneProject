"""Deterministic course matching: what the student said -> one of their registered courses.

Handles codes in any spacing or case ("cse 326", "CSE-326", "326"), titles and partial titles
("computer networks", "networks"), and acronyms ("dbms", "os"). Never guesses between two
equally good matches; the reply asks instead.
"""

import re
from dataclasses import dataclass, field
from typing import Any

_CODE = re.compile(r"^\s*([A-Za-z]{2,4})\s*-?\s*(\d{3})\s*$")
_DIGITS = re.compile(r"^\s*(\d{3})\s*$")
_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"and", "of", "the", "in", "for", "to", "a", "an", "course", "class", "subject", "lab"}


def normalise_code(text: str) -> str | None:
    """'cse 326' / 'CSE-326' / ' cse326 ' -> 'CSE326'; anything else -> None."""
    match = _CODE.match(text)
    return f"{match.group(1).upper()}{match.group(2)}" if match else None


def spoken_code(code: str) -> str:
    """'CSE326' -> 'CSE 326', which text-to-speech reads as letters then a number."""
    match = re.match(r"^([A-Z]+)(\d+)$", code)
    return f"{match.group(1)} {match.group(2)}" if match else code


def _words(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if w not in _STOP]


# Compound words students abbreviate with two letters: "Database Management Systems" -> DBMS.
_ACRONYM_PARTS = {"database": "db"}


def _acronyms(title: str) -> set[str]:
    words = _words(title)
    return {
        "".join(w[0] for w in words),
        "".join(_ACRONYM_PARTS.get(w, w[0]) for w in words),
    }


def _word_matches(said: str, title_words: list[str]) -> bool:
    # "network" matches "networks"; "algo" matches "algorithms"
    return any(t.startswith(said) or said.startswith(t) for t in title_words if len(said) >= 3)


@dataclass
class CourseMatch:
    course: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = field(default_factory=list)

    @property
    def ambiguous(self) -> bool:
        return self.course is None and len(self.candidates) > 1


def match_course(mention: str | None, courses: list[dict[str, Any]]) -> CourseMatch:
    """`courses` are attendance rows with `course_code` and `course_title`."""
    if not mention or not mention.strip():
        return CourseMatch()

    if code := normalise_code(mention):
        exact = [c for c in courses if c["course_code"] == code]
        return CourseMatch(course=exact[0]) if exact else CourseMatch()

    if digits := _DIGITS.match(mention):
        found = [c for c in courses if c["course_code"].endswith(digits.group(1))]
        return CourseMatch(course=found[0]) if len(found) == 1 else CourseMatch(candidates=found)

    said = _words(mention)
    if not said:
        return CourseMatch()

    if len(said) == 1:
        by_acronym = [c for c in courses if said[0] in _acronyms(c["course_title"])]
        if len(by_acronym) == 1:
            return CourseMatch(course=by_acronym[0])

    scored: list[tuple[float, dict[str, Any]]] = []
    for course in courses:
        title_words = _words(course["course_title"])
        hits = sum(_word_matches(w, title_words) for w in said)
        score = hits / len(said)
        if score >= 0.5:
            scored.append((score, course))
    if not scored:
        return CourseMatch()
    best = max(score for score, _ in scored)
    top = [course for score, course in scored if score == best]
    return CourseMatch(course=top[0]) if len(top) == 1 else CourseMatch(candidates=top)
