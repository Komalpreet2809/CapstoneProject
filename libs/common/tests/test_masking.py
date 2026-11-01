import re

import pytest

from voiceserve_common.masking import MASK, REDACTED, mask_identifier, mask_text, mask_value

TEXT_CASES = [
    # phone numbers in the ways people write and STT emits them
    ("call me on 9876543210", f"call me on {MASK}10"),
    ("call me on 98765 43210", f"call me on {MASK}10"),
    ("call me on 98765-43210", f"call me on {MASK}10"),
    ("call me on 987 654 3210", f"call me on {MASK}10"),
    ("call me on +91 98765 43210", f"call me on {MASK}10"),
    ("call me on +91-9876543210", f"call me on {MASK}10"),
    ("call me on 09876543210", f"call me on {MASK}10"),
    ("call me on 919876543210", f"call me on {MASK}10"),
    # numeric IDs and OTPs: any run of 6+ digits
    ("student 12215678 asked", f"student {MASK}78 asked"),
    ("otp is 482913", f"otp is {MASK}13"),
    ("otp is १२३४५६", f"otp is {MASK}५६"),  # Devanagari digits
    (
        "/attendance?student_id=12215678&course=CSE326",
        f"/attendance?student_id={MASK}78&course=CSE326",
    ),
    # things that must survive: ticket IDs, dates, times, course codes, small amounts, latencies
    ("ticket 48213 is OPEN", "ticket 48213 is OPEN"),
    ("leave 2026-11-01 to 2026-11-05", "leave 2026-11-01 to 2026-11-05"),
    ("class at 14:30 in room 412", "class at 14:30 in room 412"),
    ("course CSE326 attendance 78%", "course CSE326 attendance 78%"),
    ("ttfa 1234 ms", "ttfa 1234 ms"),
    ("", ""),
]


@pytest.mark.parametrize(("raw", "expected"), TEXT_CASES)
def test_mask_text(raw: str, expected: str) -> None:
    assert mask_text(raw) == expected


@pytest.mark.parametrize("raw", [case[0] for case in TEXT_CASES])
def test_mask_text_leaves_no_long_digit_runs(raw: str) -> None:
    assert not re.search(r"\d{6,}", mask_text(raw))


def test_masks_are_fixed_width() -> None:
    assert mask_text("12345678901234") == mask_text("1234567834")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("DEMO001", f"{MASK}01"), ("12215678", f"{MASK}78"), ("ab", MASK), ("", MASK)],
)
def test_mask_identifier(raw: str, expected: str) -> None:
    assert mask_identifier(raw) == expected


def test_mask_value_structured() -> None:
    event = {
        "student_id": "DEMO001",
        "phone_mock": 9876543210,
        "otp": "482913",
        "session_token": "eyJhbGciOi.payload.sig",
        "Authorization": "Bearer abc",
        "X-Service-Token": "svc-123",
        "course_code": "CSE326",
        "ticket_id": "48213",
        "note": "my number is 98765 43210",
        "turns": [{"text": "otp 111222", "student_id": "12215678"}],
        "latency_ms": 812,
    }
    assert mask_value(event) == {
        "student_id": f"{MASK}01",
        "phone_mock": f"{MASK}10",
        "otp": REDACTED,
        "session_token": REDACTED,
        "Authorization": REDACTED,
        "X-Service-Token": REDACTED,
        "course_code": "CSE326",
        "ticket_id": "48213",
        "note": f"my number is {MASK}10",
        "turns": [{"text": f"otp {MASK}22", "student_id": f"{MASK}78"}],
        "latency_ms": 812,
    }


def test_mask_value_list_under_id_key() -> None:
    assert mask_value({"phone": ["9876543210", "9123456789"]}) == {
        "phone": [f"{MASK}10", f"{MASK}89"]
    }


def test_mask_value_none_under_id_key_stays_none() -> None:
    assert mask_value({"student_id": None}) == {"student_id": None}


def test_mask_value_does_not_mutate_input() -> None:
    event = {"student_id": "DEMO001"}
    mask_value(event)
    assert event == {"student_id": "DEMO001"}
