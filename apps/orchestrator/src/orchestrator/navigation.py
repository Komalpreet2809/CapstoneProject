"""Navigate: what the student said -> one entry of the portal's menu catalogue (brief §5).

Deterministic, like course matching: labels and keywords from the Mini UMS catalogue are
compared word by word. An exact label or keyword wins; otherwise the entry covering the most
of the student's words wins, shorter labels first. Two equally good entries are never guessed
between; the reply asks instead.
"""

import re
from dataclasses import dataclass, field
from typing import Any

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "my", "a", "an", "of", "for", "to", "page", "pages", "section", "menu", "tab",
    "portal", "please", "and", "screen", "option", "ums", "me", "view",
}  # fmt: skip
EXACT, KEYWORD, THRESHOLD = 100.0, 90.0, 50.0


@dataclass(frozen=True)
class MenuEntry:
    id: str
    label: str
    href: str
    path: str  # "Administrative › Fee" for the card
    keywords: tuple[str, ...] = ()


@dataclass
class NavMatch:
    entry: MenuEntry | None = None
    candidates: list[MenuEntry] = field(default_factory=list)

    @property
    def ambiguous(self) -> bool:
        return self.entry is None and len(self.candidates) > 1


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def words(text: str) -> list[str]:
    return [_stem(w) for w in _WORD.findall(text.lower().replace("&", " and ")) if w not in _STOP]


def entries_from_catalogue(catalogue: dict[str, Any]) -> list[MenuEntry]:
    out = []
    for menu in catalogue["menu"]:
        for group in menu["groups"]:
            for e in group["entries"]:
                out.append(
                    MenuEntry(
                        id=e["id"],
                        label=e["label"],
                        href=e.get("route") or f"/m/{e['id']}",
                        path=f"{menu['label']} › {group['label']}",
                        keywords=tuple(e.get("keywords") or ()),
                    )
                )
    return out


def _score(said: list[str], entry: MenuEntry) -> float:
    label = words(entry.label)
    if said == label:
        return EXACT
    if any(said == words(k) for k in entry.keywords):
        return KEYWORD
    vocab = set(label) | {w for k in entry.keywords for w in words(k)}
    covered = sum(w in vocab for w in said) / len(said)
    if covered == 0:
        return 0.0
    # Of entries covering the same share of what was said, prefer labels with fewer extra words,
    # then entries whose curated keywords include the words said ("hostel leave" -> Application,
    # not Slip, because "leave" is the Application's keyword).
    extra = len(set(label) - set(said))
    keyword_words = {w for k in entry.keywords for w in words(k)}
    return 80.0 * covered - 2.0 * extra + 1.0 * sum(w in keyword_words for w in said)


def match_page(said: str, entries: list[MenuEntry]) -> NavMatch:
    target = words(said)
    if not target:
        return NavMatch()
    scored = sorted(((_score(target, e), e) for e in entries), key=lambda p: -p[0])
    best = scored[0][0]
    if best < THRESHOLD:
        return NavMatch()
    tied = [e for s, e in scored if s == best]
    if len(tied) == 1:
        return NavMatch(entry=tied[0])
    return NavMatch(candidates=tied[:3])
