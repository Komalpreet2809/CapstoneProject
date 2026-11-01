"""The student's own data: courses, attendance, timetable, fees, exams, assignments, drives."""

from collections.abc import Awaitable, Callable
from datetime import timedelta

import httpx

from mini_ums_api.rules import campus_today

Login = Callable[[str], Awaitable[dict[str, str]]]


async def test_courses_carry_attendance(client: httpx.AsyncClient, login: Login) -> None:
    courses = (await client.get("/me/courses", headers=await login("24100001"))).json()
    assert len(courses) == 7
    below = [c for c in courses if not c["attendance"]["meets_threshold"]]
    assert len(below) == 1  # Aarav: one course under 75%
    assert below[0]["attendance"]["classes_needed"] > 0
    assert {"code", "title", "term", "roll_no", "group_no", "faculty"} <= set(courses[0])


async def test_attendance_boundary_is_exact(client: httpx.AsyncClient, login: Login) -> None:
    items = (await client.get("/me/attendance", headers=await login("24100004"))).json()
    on_the_line = [a for a in items if a["percent"] == 75.0]
    assert len(on_the_line) == 1
    assert on_the_line[0]["meets_threshold"] is True
    assert on_the_line[0]["can_miss"] == 0


async def test_attendance_filter_normalises_course_code(
    client: httpx.AsyncClient, login: Login
) -> None:
    headers = await login("24100001")
    items = (await client.get("/me/attendance?course=cse326", headers=headers)).json()
    assert [a["course_code"] for a in items] == ["CSE326"]


async def test_fees(client: httpx.AsyncClient, login: Login) -> None:
    aarav = (await client.get("/me/fees", headers=await login("24100001"))).json()
    assert aarav["total_due"] == 23500 and aarav["overdue_due"] == 0
    simran = (await client.get("/me/fees", headers=await login("24100002"))).json()
    assert simran["total_due"] == 0
    rohan = (await client.get("/me/fees", headers=await login("24100003"))).json()
    assert rohan["overdue_due"] == 30000
    assert any(i["overdue"] for i in rohan["items"])


async def test_timetable_for_a_day_and_after_a_time(
    client: httpx.AsyncClient, login: Login
) -> None:
    headers = await login("24100001")
    monday = campus_today() - timedelta(days=campus_today().weekday())
    day = (await client.get(f"/me/timetable?date={monday}", headers=headers)).json()
    assert day["weekday"] == "Monday"
    starts = [e["start"] for e in day["entries"]]
    assert starts == sorted(starts)
    later = (await client.get(f"/me/timetable?date={monday}&after=14:00", headers=headers)).json()
    assert all(e["start"] >= "14:00:00" for e in later["entries"])
    sunday = monday + timedelta(days=6)
    assert (await client.get(f"/me/timetable?date={sunday}", headers=headers)).json()[
        "entries"
    ] == []


async def test_exams_have_seating_for_upcoming_papers(
    client: httpx.AsyncClient, login: Login
) -> None:
    exams = (await client.get("/me/exams", headers=await login("24100001"))).json()
    today = campus_today().isoformat()
    upcoming = [x for x in exams if x["date"] >= today]
    assert upcoming and all(x["seating"] for x in upcoming)


async def test_pending_assignments(client: httpx.AsyncClient, login: Login) -> None:
    headers = await login("24100001")
    pending = (await client.get("/me/assignments", headers=headers)).json()
    every = (await client.get("/me/assignments?status=all", headers=headers)).json()
    assert pending and len(every) > len(pending)
    assert all(not a["submitted"] and a["days_left"] >= 0 for a in pending)


async def test_messages_and_content(client: httpx.AsyncClient, login: Login) -> None:
    messages = (await client.get("/me/messages?limit=3", headers=await login("24100001"))).json()
    assert len(messages) == 3
    assert (await client.get("/content/news")).status_code == 200
    kinds = {a["kind"] for a in (await client.get("/content/announcements")).json()}
    assert kinds == {"ribbon", "banner"}


async def test_placement_drives_eligibility_and_acknowledgement(
    client: httpx.AsyncClient, login: Login
) -> None:
    headers = await login("24100001")
    pending = (await client.get("/me/placement-drives?pending_only=true", headers=headers)).json()
    assert len(pending) == 4  # CS, CGPA 8.1
    first, second = pending[0]["id"], pending[1]["id"]
    for drive, action in [(first, "read"), (second, "later")]:
        ack = await client.post(
            "/me/placement-drives/ack",
            json={"drive_ids": [drive], "action": action},
            headers=headers,
        )
        assert ack.status_code == 204
    still = (await client.get("/me/placement-drives?pending_only=true", headers=headers)).json()
    assert {d["id"] for d in still} == {d["id"] for d in pending} - {first, second}

    rohan = (await client.get("/me/placement-drives", headers=await login("24100003"))).json()
    assert [d["company"] for d in rohan] == ["Helioforge Engineering"]  # ME, CGPA 6.3


async def test_acknowledging_an_ineligible_drive_fails(
    client: httpx.AsyncClient, login: Login
) -> None:
    response = await client.post(
        "/me/placement-drives/ack",
        json={"drive_ids": [999], "action": "read"},
        headers=await login("24100003"),
    )
    assert response.status_code == 404


async def test_catalogue(client: httpx.AsyncClient) -> None:
    menu = (await client.get("/catalogue/menu")).json()
    assert len(menu["menu"]) == 5 and menu["shortcuts"] and menu["sidebar"]
    rms = (await client.get("/catalogue/rms")).json()
    assert len(rms["declarations"]["items"]) == 5
    assert (await client.get("/catalogue/policies")).json()["attendance_min_percent"] == 75
