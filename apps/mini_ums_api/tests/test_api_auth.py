"""Login, lockout, sessions, and the identity rule (rule 1)."""

from collections.abc import Awaitable, Callable

import httpx

from mini_ums_api.main import create_app
from mini_ums_api.seed.personas import PERSONA_PASSWORD
from mini_ums_api.settings import Settings

Login = Callable[[str], Awaitable[dict[str, str]]]


async def test_login_returns_token_and_profile(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/auth/login", json={"reg_no": "24100002", "password": PERSONA_PASSWORD}
    )
    body = response.json()
    assert response.status_code == 200
    assert body["token"]
    assert body["student"]["name"] == "Simran Kaur"
    assert body["student"]["password_expires_in_days"] == 5
    assert "password_hash" not in body["student"]


async def test_wrong_password_and_unknown_student_look_the_same(client: httpx.AsyncClient) -> None:
    wrong = await client.post("/auth/login", json={"reg_no": "24100001", "password": "nope"})
    unknown = await client.post("/auth/login", json={"reg_no": "24999999", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


async def test_malformed_registration_number(client: httpx.AsyncClient) -> None:
    response = await client.post("/auth/login", json={"reg_no": "abc", "password": "x"})
    assert response.status_code == 422


async def test_locked_persona_cannot_log_in(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/auth/login", json={"reg_no": "24100005", "password": PERSONA_PASSWORD}
    )
    assert response.status_code == 423


async def test_lockout_after_repeated_failures(client: httpx.AsyncClient) -> None:
    attempt = {"reg_no": "24110003", "password": "wrong"}
    codes = [(await client.post("/auth/login", json=attempt)).status_code for _ in range(6)]
    assert codes == [401, 401, 401, 401, 423, 423]


async def test_logout_ends_the_session(client: httpx.AsyncClient, login: Login) -> None:
    headers = await login("24100006")
    assert (await client.get("/me", headers=headers)).status_code == 200
    assert (await client.post("/auth/logout", headers=headers)).status_code == 204
    assert (await client.get("/me", headers=headers)).status_code == 401


async def test_personal_routes_need_a_session(client: httpx.AsyncClient) -> None:
    for path in ["/me", "/me/fees", "/me/tickets", "/me/hostel-leaves"]:
        assert (await client.get(path)).status_code == 401
    bad = {"Authorization": "Bearer not-a-real-token"}
    assert (await client.get("/me", headers=bad)).status_code == 401


async def test_naming_another_student_is_refused(client: httpx.AsyncClient, login: Login) -> None:
    headers = await login("24100006")
    for param in ["student_id", "reg_no"]:
        other = await client.get(f"/me/fees?{param}=24100001", headers=headers)
        own = await client.get(f"/me/fees?{param}=24100006", headers=headers)
        assert other.status_code == 403
        assert own.status_code == 200


async def test_bodies_cannot_carry_an_identity(client: httpx.AsyncClient, login: Login) -> None:
    headers = await login("24100006")
    body = {"note": "hello there", "student_id": "24100001"}
    response = await client.post("/me/tickets/10019/notes", json=body, headers=headers)
    assert response.status_code == 422


async def test_other_students_tickets_are_invisible(
    client: httpx.AsyncClient, login: Login
) -> None:
    headers = await login("24100006")  # 10019 belongs to Aarav
    assert (await client.get("/me/tickets/10019", headers=headers)).status_code == 404


async def test_demo_accounts_only_in_dev(client: httpx.AsyncClient) -> None:
    response = await client.get("/dev/demo-accounts")
    assert response.status_code == 200
    assert {a["reg_no"] for a in response.json()} >= {"24100001", "24100005"}

    prod = create_app(Settings(environment="prod"), checks={})
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=prod), base_url="http://test"
    ) as c:
        assert (await c.get("/dev/demo-accounts")).status_code == 404
