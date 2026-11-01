from datetime import date

import pytest

from mini_ums_api.rules import attendance_summary, password_expires_in_days

# (held, attended) -> (percent, meets, classes_needed, can_miss) at a 75% threshold
CASES = [
    ((40, 30), (75.0, True, 0, 0)),  # exactly on the line counts as meeting it
    ((40, 29), (72.5, False, 4, 0)),  # (29+4)/(40+4) = 75%
    ((40, 31), (77.5, True, 0, 1)),  # 31/41 = 75.6% still ok, 31/42 not
    ((40, 40), (100.0, True, 0, 13)),  # 40/53 = 75.47%
    ((4, 0), (0.0, False, 12, 0)),  # 12/16 = 75%
    ((3, 2), (66.67, False, 1, 0)),
    ((0, 0), (None, None, 0, 0)),  # no classes yet
]


@pytest.mark.parametrize(("counts", "expected"), CASES)
def test_attendance_summary(counts: tuple[int, int], expected: tuple[object, ...]) -> None:
    s = attendance_summary(*counts, 75)
    assert (s.percent, s.meets_threshold, s.classes_needed, s.can_miss) == expected


def test_classes_needed_is_minimal() -> None:
    for held in range(1, 60):
        for attended in range(held + 1):
            s = attendance_summary(held, attended, 75)
            k = s.classes_needed
            assert (attended + k) * 4 >= 3 * (held + k)
            if k > 0:
                assert (attended + k - 1) * 4 < 3 * (held + k - 1)
            m = s.can_miss
            assert attended * 4 >= 3 * (held + m) or (m == 0 and not s.meets_threshold)


@pytest.mark.parametrize(("held", "attended"), [(-1, 0), (10, 11), (10, -1)])
def test_rejects_impossible_counts(held: int, attended: int) -> None:
    with pytest.raises(ValueError):
        attendance_summary(held, attended, 75)


@pytest.mark.parametrize("threshold", [0, 100, 120])
def test_rejects_bad_threshold(threshold: float) -> None:
    with pytest.raises(ValueError):
        attendance_summary(10, 5, threshold)


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        (date(2026, 11, 1), 90),
        (date(2026, 8, 8), 5),
        (date(2026, 8, 3), 0),
        (date(2026, 7, 1), -33),
    ],
)
def test_password_expiry(changed: date, expected: int) -> None:
    assert password_expires_in_days(changed, date(2026, 11, 1), 90) == expected
