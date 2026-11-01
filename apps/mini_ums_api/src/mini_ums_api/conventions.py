"""Typed access to conventions.yaml, validated once at import.

A malformed or inconsistent conventions file fails loudly at startup (and in tests) rather
than at request time: duplicate menu IDs, shortcuts pointing at missing entries, and RMS
categories without sub-categories are all rejected here.
"""

from functools import cache
from importlib.resources import files

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Policies(_Model):
    attendance_min_percent: float = Field(gt=0, lt=100)
    password_max_age_days: int
    login_max_failures: int
    login_lockout_minutes: int
    session_hours: int
    hostel_leave_max_days: int
    placement_remind_later_hours: int


class Programme(_Model):
    code: str
    name: str
    school: str


class HostelBlocks(_Model):
    boys: list[str]
    girls: list[str]


class Declarations(_Model):
    version: str
    items: list[str] = Field(min_length=1)


class RmsCategory(_Model):
    id: str
    label: str
    dept: str
    needs_location: bool
    sub_categories: list[str] = Field(min_length=1)


class Rms(_Model):
    declarations: Declarations
    categories: list[RmsCategory]

    def category(self, category_id: str) -> RmsCategory | None:
        return next((c for c in self.categories if c.id == category_id), None)


class MenuEntry(_Model):
    id: str
    label: str
    route: str | None = None
    keywords: list[str] = []


class MenuGroup(_Model):
    label: str
    entries: list[MenuEntry]


class Menu(_Model):
    id: str
    label: str
    groups: list[MenuGroup]


class Conventions(_Model):
    version: int
    ids: dict[str, dict[str, str | int]]
    policies: Policies
    programmes: list[Programme]
    hostel_blocks: HostelBlocks
    rms: Rms
    sidebar: list[str]
    shortcuts: list[str]
    menu: list[Menu]

    def entries(self) -> list[MenuEntry]:
        return [e for m in self.menu for g in m.groups for e in g.entries]

    @model_validator(mode="after")
    def _consistent(self) -> "Conventions":
        ids = [e.id for e in self.entries()]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"duplicate menu entry ids: {duplicates}")
        missing = [i for i in self.sidebar + self.shortcuts if i not in set(ids)]
        if missing:
            raise ValueError(f"sidebar/shortcuts reference unknown entries: {missing}")
        return self


def load_conventions(text: str) -> Conventions:
    return Conventions.model_validate(yaml.safe_load(text))


@cache
def conventions() -> Conventions:
    text = files("mini_ums_api").joinpath("conventions.yaml").read_text(encoding="utf-8")
    return load_conventions(text)
