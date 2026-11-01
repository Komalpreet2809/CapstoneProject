import re

import pytest
import yaml
from pydantic import ValidationError

from mini_ums_api.conventions import conventions, load_conventions


def test_shipped_conventions_are_valid() -> None:
    c = conventions()
    assert len(c.menu) == 5
    assert [m.label for m in c.menu] == [
        "Academics",
        "Administrative",
        "Important Links",
        "Student Services",
        "Quick Links",
    ]
    # Mirrors the real portal's catalogue (docs/reference/ums-structure.md).
    assert len(c.entries()) >= 150
    assert all(g.entries for m in c.menu for g in m.groups)
    assert len(c.rms.declarations.items) == 5
    assert re.fullmatch(str(c.ids["reg_no"]["pattern"]), str(c.ids["reg_no"]["example"]))


def test_real_pages_are_routed() -> None:
    routes = {e.id: e.route for e in conventions().entries() if e.route}
    assert routes == {
        "rms-log-request": "/rms",
        "rms-history": "/rms?tab=history",
        "student-attendance": "/attendance",
        "dashboard": "/",
    }


def _raw() -> dict[str, object]:
    from importlib.resources import files

    data: dict[str, object] = yaml.safe_load(
        files("mini_ums_api").joinpath("conventions.yaml").read_text(encoding="utf-8")
    )
    return data


def test_duplicate_menu_ids_are_rejected() -> None:
    raw = _raw()
    menu = raw["menu"]
    assert isinstance(menu, list)
    menu[0]["groups"][0]["entries"].append({"id": "fee-dashboard", "label": "Again"})
    with pytest.raises(ValidationError, match="duplicate menu entry ids"):
        load_conventions(yaml.safe_dump(raw))


def test_unknown_shortcut_is_rejected() -> None:
    raw = _raw()
    raw["shortcuts"] = ["does-not-exist"]
    with pytest.raises(ValidationError, match="unknown entries"):
        load_conventions(yaml.safe_dump(raw))
