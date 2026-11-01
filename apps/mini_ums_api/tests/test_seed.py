from datetime import date
from functools import cache

from mini_ums_api.ids import is_valid_number
from mini_ums_api.seed.generate import Dataset, generate, stats
from mini_ums_api.seed.personas import PERSONAS

TODAY = date(2026, 11, 1)


@cache
def _ds(seed: int = 42, n: int = 600) -> Dataset:
    return generate(seed, TODAY, n)


def _persona_rows(ds: Dataset) -> dict[str, list[dict[str, object]]]:
    ids = {p.reg_no for p in PERSONAS}
    return {
        table: [r for r in rows if r.get("reg_no") in ids]
        for table, rows in ds.tables.items()
        if rows and "reg_no" in rows[0]
    }


def test_same_inputs_same_dataset() -> None:
    assert generate(42, TODAY, 60).tables == generate(42, TODAY, 60).tables


def test_personas_do_not_depend_on_population_seed_or_size() -> None:
    assert _persona_rows(generate(1, TODAY, 40)) == _persona_rows(generate(2, TODAY, 90))


def test_distributions_stay_in_documented_ranges() -> None:
    s = stats(_ds())
    assert 0.20 <= s["share_below_threshold_overall"] <= 0.35
    assert 0.08 <= s["share_with_overdue_fees"] <= 0.25
    assert 0.05 <= s["share_enrolments_without_marks"] <= 0.25
    assert 0.50 <= s["share_tickets_hostel_or_it"] <= 0.75
    assert s["tickets"] >= 150


def test_referential_integrity() -> None:
    ds = _ds()
    students = {r["reg_no"] for r in ds.rows("students")}
    courses = {r["code"] for r in ds.rows("courses")}
    tickets = {r["number"] for r in ds.rows("tickets")}
    assert all(
        r["reg_no"] in students and r["course_code"] in courses for r in ds.rows("enrollments")
    )
    assert all(r["ticket_number"] in tickets for r in ds.rows("ticket_events"))
    assert all(is_valid_number(n) for n in tickets)
    assert len({r["vid"] for r in ds.rows("students")}) == len(students)


def test_correlation_attendance_vs_marks() -> None:
    ds = _ds()
    ratio: dict[str, list[float]] = {}
    for a in ds.rows("attendance"):
        ratio.setdefault(a["reg_no"], []).append(a["attended"] / a["held"])
    marks: dict[str, list[float]] = {}
    for m in ds.rows("marks"):
        marks.setdefault(m["reg_no"], []).append(float(m["score"] / m["max_score"]))
    pairs = [(sum(ratio[k]) / len(ratio[k]), sum(v) / len(v)) for k, v in marks.items()]
    n = len(pairs)
    mx, my = sum(p[0] for p in pairs) / n, sum(p[1] for p in pairs) / n
    cov = sum((x - mx) * (y - my) for x, y in pairs)
    sx = sum((x - mx) ** 2 for x, _ in pairs) ** 0.5
    sy = sum((y - my) ** 2 for _, y in pairs) ** 0.5
    assert cov / (sx * sy) > 0.4


def test_deliberate_edge_cases_exist() -> None:
    ds = _ds()
    students = {r["reg_no"]: r for r in ds.rows("students")}
    assert students["24100005"]["locked_until"] is not None
    names = [r["name"] for r in ds.rows("students")]
    assert "Ananya Gupta" in names and "Anaya Gupta" in names
    meera = [a for a in ds.rows("attendance") if a["reg_no"] == "24100004"]
    assert any(a["attended"] * 4 == a["held"] * 3 for a in meera)  # exactly 75.00%
    open_plumbing = [
        t
        for t in ds.rows("tickets")
        if t["reg_no"] == "24100004" and t["sub_category"] == "Plumbing" and t["status"] != "CLOSED"
    ]
    assert len(open_plumbing) == 2
    assert any(t["status"] == "REOPENED" for t in ds.rows("tickets"))


def test_synthetic_contact_details_cannot_be_real() -> None:
    for s in _ds().rows("students"):
        assert s["phone_mock"].startswith("+91 50")  # Indian mobiles never start with 5
        assert s["email_mock"].endswith("@students.univra.example")  # reserved TLD
