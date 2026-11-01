from datetime import datetime

import pytest

from mini_ums_api.ids import (
    damm_check_digit,
    is_valid_number,
    number_from_request_id,
    request_id,
    speakable,
    ticket_number,
)


@pytest.mark.parametrize(("digits", "check"), [("572", 4), ("1001", 9), ("0", 0), ("5724", 0)])
def test_damm_check_digit_known_values(digits: str, check: int) -> None:
    assert damm_check_digit(digits) == check


def test_every_ticket_number_validates() -> None:
    assert all(is_valid_number(ticket_number(seq)) for seq in range(1000, 10000))


def test_single_digit_errors_are_caught() -> None:
    for seq in range(1000, 10000, 37):
        number = ticket_number(seq)
        for pos in range(5):
            for d in "0123456789":
                if d != number[pos]:
                    assert not is_valid_number(number[:pos] + d + number[pos + 1 :])


def test_adjacent_transpositions_are_caught() -> None:
    for seq in range(1000, 10000, 37):
        number = ticket_number(seq)
        for pos in range(4):
            a, b = number[pos], number[pos + 1]
            if a != b:
                swapped = number[:pos] + b + a + number[pos + 2 :]
                assert not is_valid_number(swapped)


@pytest.mark.parametrize("seq", [999, 10000, -1])
def test_sequence_out_of_range(seq: int) -> None:
    with pytest.raises(ValueError):
        ticket_number(seq)


def test_request_id_format() -> None:
    assert request_id("HST", datetime(2026, 11, 3), "10019") == "HST/Nov-26/10019"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("HST/Nov-26/10019", "10019"),
        ("10019", "10019"),
        (" 10019 ", "10019"),
        ("HST/Nov-26/10018", None),  # wrong check digit
        ("10091", None),  # last two digits transposed
        ("1001", None),
        ("abcde", None),
        ("१००१७", None),  # Devanagari digits are not accepted as IDs
    ],
)
def test_number_from_request_id(raw: str, expected: str | None) -> None:
    assert number_from_request_id(raw) == expected


def test_speakable() -> None:
    assert speakable("10019") == "1 0 0 1 9"
