"""RMS end to end: declarations, idempotency, duplicate check, notes, feedback, reopening.

Each test uses its own persona or sub-category so tests stay independent.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

import httpx

from mini_ums_api.conventions import conventions
from mini_ums_api.ids import is_valid_number
from mini_ums_api.rules import campus_today

Login = Callable[[str], Awaitable[dict[str, str]]]


def new_key() -> dict[str, str]:
    return {"Idempotency-Key": f"test-{uuid.uuid4()}"}


VERSION = conventions().rms.declarations.version


def ticket(**overrides: Any) -> dict[str, Any]:
    body = {
        "category": "HOSTEL",
        "sub_category": "Carpentry",
        "block": "GH-2",
        "room": "118",
        "title": "Window latch broken",
        "description": "The window latch is broken and the window does not close.",
        "declaration_version": VERSION,
    }
    return body | overrides


async def test_log_request_end_to_end(client: httpx.AsyncClient, login: Login) -> None:
    headers = await login("24100002")
    created = await client.post("/me/tickets", json=ticket(), headers=headers | new_key())
    assert created.status_code == 201, created.text
    t = created.json()
    assert is_valid_number(t["number"])
    assert t["request_id"] == f"HST/{campus_today():%b-%y}/{t['number']}"
    assert t["speakable"] == " ".join(t["number"])
    assert t["status"] == "OPEN"

    history = (await client.get("/me/tickets", headers=headers)).json()
    assert history["tickets"][0]["number"] == t["number"]
    assert history["counts"]["open"] >= 1

    detail = (await client.get(f"/me/tickets/{t['number']}", headers=headers)).json()
    assert [e["status_to"] for e in detail["events"]] == ["OPEN"]

    noted = await client.post(
        f"/me/tickets/{t['number']}/notes",
        json={"note": "Also the curtain rod is loose."},
        headers=headers,
    )
    assert noted.status_code == 200
    assert noted.json()["events"][-1]["note"] == "Also the curtain rod is loose."


async def test_retry_with_same_key_returns_the_original(
    client: httpx.AsyncClient, login: Login
) -> None:
    headers = await login("24100002") | new_key()
    body = ticket(
        sub_category="Furniture",
        title="Chair broken",
        description="The study chair has a cracked seat.",
    )
    first = await client.post("/me/tickets", json=body, headers=headers)
    retry = await client.post("/me/tickets", json=body, headers=headers)
    assert (first.status_code, retry.status_code) == (201, 200)
    assert first.json()["number"] == retry.json()["number"]
    history = (await client.get("/me/tickets", headers=headers)).json()["tickets"]
    assert sum(t["title"] == "Chair broken" for t in history) == 1


async def test_reusing_a_key_for_a_different_request_fails(
    client: httpx.AsyncClient, login: Login
) -> None:
    headers = await login("24100002") | new_key()
    body = ticket(
        category="LIBRARY",
        sub_category="Account Issue",
        block=None,
        room=None,
        title="Library account blocked",
        description="My library account is blocked and I cannot issue books.",
    )
    assert (await client.post("/me/tickets", json=body, headers=headers)).status_code == 201
    changed = body | {"title": "Something else entirely"}
    assert (await client.post("/me/tickets", json=changed, headers=headers)).status_code == 422


async def test_similar_open_request_is_offered_instead(
    client: httpx.AsyncClient, login: Login
) -> None:
    headers = await login("24100001")  # Aarav already has an open IT / Wi-Fi request (10019)
    body = ticket(
        category="IT",
        sub_category="Wi-Fi",
        block="BH-3",
        room="412",
        title="Wi-Fi down again",
        description="Wi-Fi is not working in my room again.",
    )
    duplicate = await client.post("/me/tickets", json=body, headers=headers | new_key())
    assert duplicate.status_code == 409
    assert duplicate.json()["similar"]["number"] == "10019"

    forced = await client.post(
        "/me/tickets", json=body | {"allow_duplicate": True}, headers=headers | new_key()
    )
    assert forced.status_code == 201


async def test_declarations_and_fields_are_validated(
    client: httpx.AsyncClient, login: Login
) -> None:
    headers = await login("24100002")
    bad_bodies = [
        ticket(declaration_version="old"),  # declarations not accepted (rule 10)
        ticket(block=None),  # hostel needs a location
        ticket(category="NOPE"),
        ticket(sub_category="Electrical", category="LIBRARY", block=None, room=None),
        ticket(description="short"),
        ticket(student_id="24100001"),  # identity can't ride in the body
    ]
    for body in bad_bodies:
        response = await client.post("/me/tickets", json=body, headers=headers | new_key())
        assert response.status_code == 422, body
    missing_key = await client.post("/me/tickets", json=ticket(), headers=headers)
    assert missing_key.status_code == 422


async def test_feedback_not_resolved_reopens(client: httpx.AsyncClient, login: Login) -> None:
    headers = await login("24100001")
    closed = (await client.get("/me/tickets/10024", headers=headers)).json()
    assert closed["status"] == "CLOSED" and closed["can_give_feedback"]

    note = await client.post(
        "/me/tickets/10024/notes", json={"note": "still broken"}, headers=headers
    )
    assert note.status_code == 409  # closed requests reopen only through feedback

    response = await client.post(
        "/me/tickets/10024/feedback",
        json={"resolved": False, "rating": 2, "comment": "The light failed again."},
        headers=headers,
    )
    reopened = response.json()
    assert response.status_code == 200
    assert reopened["status"] == "REOPENED"
    assert reopened["feedback"]["resolved"] is False
    assert reopened["events"][-1]["status_to"] == "REOPENED"

    again = await client.post(
        "/me/tickets/10024/feedback", json={"resolved": True, "rating": 5}, headers=headers
    )
    assert again.status_code == 409  # feedback only once


async def test_feedback_on_open_request_is_refused(client: httpx.AsyncClient, login: Login) -> None:
    headers = await login("24100004")
    response = await client.post(
        "/me/tickets/10043/feedback", json={"resolved": True, "rating": 4}, headers=headers
    )
    assert response.status_code == 409


async def test_latest_and_history_counts(client: httpx.AsyncClient, login: Login) -> None:
    rohan = await login("24100003")
    history = (await client.get("/me/tickets", headers=rohan)).json()
    assert history["counts"] == {"total": 1, "open": 1, "closed": 0}
    latest = (await client.get("/me/tickets/latest", headers=rohan)).json()
    assert latest["number"] == "10070"

    ananya = await login("24100006")
    assert (await client.get("/me/tickets/latest", headers=ananya)).status_code == 404


async def test_ticket_numbers_with_bad_check_digit_are_not_found(
    client: httpx.AsyncClient, login: Login
) -> None:
    headers = await login("24100001")
    assert (await client.get("/me/tickets/10018", headers=headers)).status_code == 404
    assert (await client.get("/me/tickets/abcde", headers=headers)).status_code == 422


# --- hostel leave ---------------------------------------------------------------------------


def leave(start: int, end: int, reason: str = "Going home for the weekend") -> dict[str, str]:
    today = campus_today()
    return {
        "from_date": (today + timedelta(days=start)).isoformat(),
        "to_date": (today + timedelta(days=end)).isoformat(),
        "reason": reason,
    }


async def test_hostel_leave_apply_and_retry(client: httpx.AsyncClient, login: Login) -> None:
    headers = await login("24100002") | new_key()
    first = await client.post("/me/hostel-leaves", json=leave(15, 16), headers=headers)
    retry = await client.post("/me/hostel-leaves", json=leave(15, 16), headers=headers)
    assert (first.status_code, retry.status_code) == (201, 200)
    assert first.json()["id"] == retry.json()["id"]
    assert first.json()["days"] == 2 and first.json()["status"] == "PENDING"


async def test_hostel_leave_rules(client: httpx.AsyncClient, login: Login) -> None:
    simran = await login("24100002")  # has a pending leave from day +6 to +8
    cases = [
        (leave(7, 9), 409),  # overlaps
        (leave(-2, 1), 422),  # starts in the past
        (leave(40, 75), 422),  # longer than the limit
        (leave(5, 3), 422),  # ends before it starts
    ]
    for body, expected in cases:
        response = await client.post("/me/hostel-leaves", json=body, headers=simran | new_key())
        assert response.status_code == expected, body

    rohan = await login("24100003")  # day scholar
    response = await client.post("/me/hostel-leaves", json=leave(20, 21), headers=rohan | new_key())
    assert response.status_code == 422
