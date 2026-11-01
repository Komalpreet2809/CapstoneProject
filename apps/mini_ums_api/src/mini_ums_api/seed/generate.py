"""Deterministic synthetic dataset for the Mini UMS.

Three independent random streams keep different parts stable:
- structure (programmes, courses, sections, timetable, exams, content): fixed seed, so the
  campus looks the same whatever the population seed;
- population (ordinary students and their records): the `seed` argument;
- personas: one stream per persona, so demo accounts never change when re-seeding.

All dates are relative to `today` (the anchor day), so a fresh seed always looks current.
The same (seed, today, n_students) always produces the same rows; tests check this.
"""

import random
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from faker import Faker

from mini_ums_api.conventions import conventions
from mini_ums_api.ids import ticket_number
from mini_ums_api.rules import CAMPUS_TZ, campus_today
from mini_ums_api.security import hash_password
from mini_ums_api.seed import content
from mini_ums_api.seed.personas import PERSONA_PASSWORD, PERSONAS, SIMILAR_NAME, Persona

Row = dict[str, Any]

STRUCTURE_SEED = "mini-ums-structure-v1"
INTAKE = "24"
SECTIONS_PER_PROGRAMME = 3
TUITION = {"CS": 120000, "EC": 115000, "ME": 110000, "BB": 95000, "BS": 105000}
HOSTEL_FEE, EXAM_FEE, ACTIVITY_FEE = 85000, 3500, 2500
CATEGORY_WEIGHTS = {
    "HOSTEL": 35,
    "IT": 25,
    "ACADEMIC": 12,
    "FEE": 8,
    "EXAMINATION": 6,
    "LIBRARY": 5,
    "TRANSPORT": 5,
    "OTHER": 4,
}
LOCKED_FOREVER = datetime(2099, 1, 1, tzinfo=UTC)


@dataclass
class Dataset:
    today: date
    tables: dict[str, list[Row]] = field(default_factory=dict)

    def add(self, table: str, **row: Any) -> Row:
        self.tables.setdefault(table, []).append(row)
        return row

    def rows(self, table: str) -> list[Row]:
        return self.tables.get(table, [])


@dataclass
class _Section:
    name: str
    programme: str
    courses: list[str]
    faculty: dict[str, str]
    held: dict[str, int]
    no_marks_course: str
    seats_taken: int = 0


@dataclass
class _Student:
    reg_no: str
    programme: str
    section: _Section
    hostel: tuple[str, str] | None
    ability: float
    rng: random.Random
    roll: int
    persona: Persona | None = None


def term_label(today: date) -> str:
    if today.month >= 7:
        return f"{today.year}-{(today.year + 1) % 100:02d} Odd"
    return f"{today.year - 1}-{today.year % 100:02d} Even"


def _at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=CAMPUS_TZ)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def generate(seed: int = 42, today: date | None = None, n_students: int = 600) -> Dataset:
    today = today or campus_today()
    ds = Dataset(today=today)
    term = term_label(today)
    s_rng = random.Random(STRUCTURE_SEED)
    p_rng = random.Random(seed)
    s_fake, p_fake = Faker("en_IN"), Faker("en_IN")
    s_fake.seed_instance(STRUCTURE_SEED)
    p_fake.seed_instance(seed)

    sections = _structure(ds, s_rng, s_fake, term)
    students = _students(ds, p_rng, p_fake, sections, term, n_students)
    for student in students:
        _enrol(ds, student, term)
        _fees(ds, student)
        _submissions(ds, student)
    _seating(ds, s_rng, students)
    _tickets(ds, p_rng, students)
    _hostel_leaves(ds, p_rng, students)
    _content(ds)
    return ds


# --- structure ------------------------------------------------------------------------------


def _structure(ds: Dataset, rng: random.Random, fake: Faker, term: str) -> list[_Section]:
    today = ds.today
    for p in conventions().programmes:
        ds.add("programmes", code=p.code, name=p.name, school=p.school)

    faculty = [f"F{i:03d}" for i in range(1, 37)]
    for fid in faculty:
        ds.add("faculty", id=fid, name=f"Dr. {fake.first_name()} {fake.last_name()}")

    prefix_g, number_g, title_g, kind_g = content.COMMON_COURSE
    common = f"{prefix_g}{number_g}"
    ds.add("courses", code=common, title=title_g, credits=2, kind=kind_g)
    programme_courses: dict[str, list[str]] = {}
    for programme, (prefix, items) in content.COURSES.items():
        codes = []
        for number, title, kind in items:
            code = f"{prefix}{number}"
            ds.add(
                "courses", code=code, title=title, credits=4 if kind == "Theory" else 2, kind=kind
            )
            codes.append(code)
        programme_courses[programme] = codes

    kinds = {c["code"]: c["kind"] for c in ds.rows("courses")}
    titles = {c["code"]: c["title"] for c in ds.rows("courses")}
    exam_id = 0
    for code in [*(c for codes in programme_courses.values() for c in codes), common]:
        if kinds[code] == "Theory":
            exam_id += 1
            ds.add(
                "exams",
                id=exam_id,
                course_code=code,
                term=term,
                exam_type="Mid-term",
                exam_date=today - timedelta(days=rng.randint(24, 34)),
                start_time=time(9, 30),
                end_time=time(11, 0),
            )
            exam_id += 1
            morning = rng.random() < 0.5
            ds.add(
                "exams",
                id=exam_id,
                course_code=code,
                term=term,
                exam_type="End-term",
                exam_date=today + timedelta(days=rng.randint(20, 40)),
                start_time=time(9, 30) if morning else time(14, 0),
                end_time=time(12, 30) if morning else time(17, 0),
            )
        else:
            exam_id += 1
            ds.add(
                "exams",
                id=exam_id,
                course_code=code,
                term=term,
                exam_type="Practical",
                exam_date=today + timedelta(days=rng.randint(10, 18)),
                start_time=time(10, 0),
                end_time=time(13, 0),
            )

    sections: list[_Section] = []
    assignment_id = 0
    for programme in content.COURSES:
        for n in range(1, SECTIONS_PER_PROGRAMME + 1):
            courses = [*programme_courses[programme], common]
            section = _Section(
                name=f"K{INTAKE}{programme}{n}",
                programme=programme,
                courses=courses,
                faculty={c: rng.choice(faculty) for c in courses},
                held={
                    c: rng.randint(10, 16) if kinds[c] == "Practical" else rng.randint(30, 44)
                    for c in courses
                },
                no_marks_course=rng.choice([c for c in courses if kinds[c] == "Theory"]),
            )
            sections.append(section)
            _timetable(ds, rng, section, kinds)
            for code in courses:
                # One already past its last date, one upcoming.
                for k, offset in enumerate((-rng.randint(3, 20), rng.randint(1, 21)), 1):
                    assignment_id += 1
                    kind = rng.choice(content.ASSIGNMENT_KINDS)
                    ds.add(
                        "assignments",
                        id=assignment_id,
                        course_code=code,
                        section=section.name,
                        term=term,
                        title=f"{kind} {k}",
                        kind=kind,
                        last_date=today + timedelta(days=offset),
                        max_marks=rng.choice([10, 20, 30]),
                    )
            for _ in range(5):
                subject, body = rng.choice(content.MESSAGE_TEMPLATES)
                code = rng.choice(courses)
                ds.add(
                    "messages",
                    section=section.name,
                    sender_name=next(
                        f["name"] for f in ds.rows("faculty") if f["id"] == section.faculty[code]
                    ),
                    sender_role=f"Course teacher, {code}",
                    subject=subject,
                    body=body.format(
                        course=f"{code} {titles[code]}",
                        day=rng.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
                        time=rng.choice(["10:00", "12:00", "15:00", "16:00"]),
                        room=f"B{rng.randint(1, 6)}-{rng.randint(1, 4)}0{rng.randint(1, 9)}",
                        assignment=f"{rng.choice(content.ASSIGNMENT_KINDS)} 2",
                        date=(today + timedelta(days=rng.randint(2, 12))).strftime("%d %b"),
                    ),
                    sent_at=_at(
                        today - timedelta(days=rng.randint(0, 14)),
                        rng.randint(8, 19),
                        rng.choice([0, 15, 30, 45]),
                    ),
                )
    return sections


def _timetable(ds: Dataset, rng: random.Random, section: _Section, kinds: dict[str, str]) -> None:
    hours = [9, 10, 11, 12, 14, 15, 16]
    free = {(day, hour) for day in range(1, 6) for hour in hours}
    room = f"B{rng.randint(1, 6)}-{rng.randint(1, 4)}{rng.randint(1, 20):02d}"
    for code in section.courses:
        if kinds[code] == "Practical":
            day = rng.randint(1, 5)
            free -= {(day, 14), (day, 15)}
            ds.add(
                "timetable",
                section=section.name,
                day_of_week=day,
                start_time=time(14),
                end_time=time(16),
                course_code=code,
                room=f"Lab-{rng.randint(1, 12)}",
                kind="Practical",
                mandatory=True,
            )
    for code in section.courses:
        if kinds[code] == "Practical":
            continue
        weekly = 2 if code.startswith("GEN") else 3
        for i in range(weekly):
            day, hour = rng.choice(sorted(free))
            free.discard((day, hour))
            tutorial = i == 2 and rng.random() < 0.4
            ds.add(
                "timetable",
                section=section.name,
                day_of_week=day,
                start_time=time(hour),
                end_time=time(hour + 1),
                course_code=code,
                room=room,
                kind="Tutorial" if tutorial else "Lecture",
                mandatory=code.startswith("GEN") or tutorial,
            )


# --- students -------------------------------------------------------------------------------


def _students(
    ds: Dataset,
    rng: random.Random,
    fake: Faker,
    sections: list[_Section],
    term: str,
    n_students: int,
) -> list[_Student]:
    today = ds.today
    by_name = {s.name: s for s in sections}
    blocks = conventions().hostel_blocks
    students: list[_Student] = []

    def add_student(
        reg_no: str,
        name: str,
        gender: str,
        section: _Section,
        hostel: tuple[str, str] | None,
        cgpa: float,
        language: str,
        password_hash: str,
        changed: datetime,
        vid: str,
        phone: str,
        ability: float,
        s_rng: random.Random,
        persona: Persona | None = None,
    ) -> None:
        first = name.split()[0].lower()
        ds.add(
            "students",
            reg_no=reg_no,
            vid=vid,
            name=name,
            programme_code=section.programme,
            section=section.name,
            term=term,
            cgpa=Decimal(f"{cgpa:.2f}"),
            is_hosteller=hostel is not None,
            hostel_block=hostel[0] if hostel else None,
            room=hostel[1] if hostel else None,
            phone_mock=phone,
            email_mock=f"{first}.{reg_no}@students.univra.example",
            preferred_language=language,
            password_hash=password_hash,
            password_changed_at=changed,
            failed_logins=0,
            locked_until=LOCKED_FOREVER if persona and persona.locked else None,
            is_demo=persona is not None,
        )
        section.seats_taken += 1
        students.append(
            _Student(
                reg_no,
                section.programme,
                section,
                hostel,
                ability,
                s_rng,
                section.seats_taken,
                persona,
            )
        )

    for i, p in enumerate(PERSONAS, 1):
        own = random.Random(f"persona:{p.reg_no}")
        add_student(
            p.reg_no,
            p.name,
            p.gender,
            by_name[f"K{INTAKE}{p.programme}{p.section_no}"],
            p.hostel,
            p.cgpa,
            p.language,
            hash_password(PERSONA_PASSWORD, salt=own.randbytes(16)),
            _at(today - timedelta(days=p.password_age_days), 10),
            f"V{i:05d}",
            f"+91 50000 {i:05d}",
            sum(p.attendance) / len(p.attendance),
            own,
            p,
        )

    # Population accounts share one hash of a random, never-disclosed password: they exist
    # for realism and analytics, not for logging in.
    unusable = hash_password(f"{rng.getrandbits(128):x}", salt=rng.randbytes(16))
    vids = rng.sample(range(10000, 100000), n_students)
    for i in range(n_students):
        section = sections[i % len(sections)]
        if i == 0:  # deliberate near-duplicate of a persona's name, same section
            name, gender, programme, section_no = SIMILAR_NAME
            section = by_name[f"K{INTAKE}{programme}{section_no}"]
        else:
            gender = "F" if rng.random() < 0.42 else "M"
            first = fake.first_name_female() if gender == "F" else fake.first_name_male()
            name = f"{first} {fake.last_name()}"
        hostel = None
        if rng.random() < 0.7:
            block = rng.choice(blocks.girls if gender == "F" else blocks.boys)
            hostel = (block, f"{rng.randint(1, 4)}{rng.randint(1, 30):02d}")
        ability = rng.betavariate(5, 2)
        cgpa = _clamp(4.6 + 5.0 * ability + rng.gauss(0, 0.45), 4.5, 9.9)
        add_student(
            f"{INTAKE}{110001 + i:06d}",
            name,
            gender,
            section,
            hostel,
            cgpa,
            rng.choices(["en", "hi", "pa"], weights=[50, 33, 17])[0],
            unusable,
            _at(today - timedelta(days=rng.randint(1, 120)), rng.randint(8, 22)),
            f"V{vids[i]}",
            f"+91 50{rng.randint(100, 999)} {rng.randint(10000, 99999)}",
            ability,
            random.Random(rng.getrandbits(64)),
        )
    return students


def _enrol(ds: Dataset, s: _Student, term: str) -> None:
    kinds = {c["code"]: c["kind"] for c in ds.rows("courses")}
    rng = s.rng
    for idx, code in enumerate(s.section.courses):
        held = s.section.held[code]
        if s.persona is not None:
            target = s.persona.attendance[idx % len(s.persona.attendance)]
            if target == 0.75:  # exact boundary case: make 75.00% representable
                held -= held % 4
            attended = round(target * held)
        else:
            # Centred so roughly 25-30% of students end up below the 75% line overall.
            p = _clamp(0.47 + 0.45 * s.ability + rng.gauss(0, 0.06), 0.3, 1.0)
            attended = sum(rng.random() < p for _ in range(held))
        ds.add(
            "enrollments",
            reg_no=s.reg_no,
            course_code=code,
            term=term,
            faculty_id=s.section.faculty[code],
            roll_no=f"R{s.roll:02d}",
            group_no=1 + s.roll % 2,
        )
        ds.add(
            "attendance",
            reg_no=s.reg_no,
            course_code=code,
            term=term,
            held=held,
            attended=attended,
            last_updated=_at(ds.today - timedelta(days=rng.randint(0, 3)), 18),
        )
        if code == s.section.no_marks_course:
            continue  # deliberate: some courses have no marks yet
        components = (
            [("Lab Evaluation", 50)]
            if kinds[code] == "Practical"
            else [("CA1", 30), ("CA2", 30), ("Mid-term", 50)]
        )
        for component, max_score in components:
            ratio = _clamp(rng.gauss(0.35 + 0.55 * s.ability, 0.12), 0, 1)
            score = round(ratio * max_score * 2) / 2
            ds.add(
                "marks",
                reg_no=s.reg_no,
                course_code=code,
                term=term,
                component=component,
                score=Decimal(str(score)),
                max_score=Decimal(max_score),
            )


def _fees(ds: Dataset, s: _Student) -> None:
    today, rng = ds.today, s.rng
    term_due = today - timedelta(days=45)
    tuition = TUITION[s.programme]
    heads = [("Tuition Fee", tuition, term_due), ("Student Activity Fee", ACTIVITY_FEE, term_due)]
    if s.hostel:
        heads.append(("Hostel Fee", HOSTEL_FEE, term_due))
    heads.append(("Examination Fee", EXAM_FEE, today + timedelta(days=20)))

    state = s.persona.fees if s.persona else None
    roll = rng.random()
    for head, amount, due in heads:
        paid = amount
        if due >= today:  # not yet due: some pay early
            paid = amount if state == "clear" or (state is None and rng.random() < 0.4) else 0
        elif state == "overdue" and head == "Tuition Fee":
            paid = amount - 30000
        elif state is None and head == "Tuition Fee" and roll < 0.10:
            paid = amount - rng.randrange(10000, 40001, 500)
        elif state is None and head == "Hostel Fee" and 0.10 <= roll < 0.18:
            paid = 0
        ds.add(
            "fees",
            reg_no=s.reg_no,
            head=head,
            amount=Decimal(amount),
            paid=Decimal(paid),
            due_date=due,
        )
    if state == "due_soon" and s.hostel:
        ds.add(
            "fees",
            reg_no=s.reg_no,
            head="Hostel Fee (2nd instalment)",
            amount=Decimal(20000),
            paid=Decimal(0),
            due_date=today + timedelta(days=10),
        )


def _submissions(ds: Dataset, s: _Student) -> None:
    rng = s.rng
    for a in ds.rows("assignments"):
        if a["section"] != s.section.name:
            continue
        past = a["last_date"] < ds.today
        if s.persona is not None:
            # Personas: every past item submitted (except one missed by Rohan); upcoming pending.
            missed = s.persona.reg_no == "24100003" and a["course_code"] == "MEC314"
            submit = past and not missed
        else:
            submit = rng.random() < (0.55 + 0.4 * s.ability if past else 0.25)
        if submit:
            when = a["last_date"] - timedelta(days=rng.randint(0, 4)) if past else ds.today
            ds.add(
                "submissions",
                assignment_id=a["id"],
                reg_no=s.reg_no,
                submitted_at=_at(min(when, ds.today), rng.randint(9, 23)),
            )


def _seating(ds: Dataset, rng: random.Random, students: list[_Student]) -> None:
    upcoming = [x for x in ds.rows("exams") if x["exam_date"] >= ds.today]
    for exam in upcoming:
        seat = 0
        for s in students:
            if exam["course_code"] not in s.section.courses:
                continue
            seat += 1
            block = "ABCDE"[(seat // 60) % 5]
            ds.add(
                "seating",
                exam_id=exam["id"],
                reg_no=s.reg_no,
                building=f"Academic Block {block}",
                room=f"{block}-{1 + (seat // 30) % 4}{(seat // 30) % 9 + 1:02d}",
                seat=f"R{(seat % 30) // 6 + 1}-S{seat % 6 + 1}",
            )


# --- tickets and leave ----------------------------------------------------------------------


def _tickets(ds: Dataset, rng: random.Random, students: list[_Student]) -> None:
    rms = conventions().rms
    today = ds.today
    version = rms.declarations.version
    by_reg = {s.reg_no: s for s in students}
    planned: list[dict[str, Any]] = []

    def plan(
        s: _Student,
        category: str,
        sub: str,
        text: int,
        created: datetime,
        status: str,
        closed_after_days: int | None = None,
        feedback: tuple[bool, int] | None = None,
    ) -> None:
        cat = rms.category(category)
        assert cat is not None and sub in cat.sub_categories
        title, description = content.TICKET_TEXT[sub][text % len(content.TICKET_TEXT[sub])]
        block = room = None
        if cat.needs_location:
            block, room = s.hostel or (
                f"AB-{rng.randint(1, 6)}",
                f"{rng.randint(1, 4)}0{rng.randint(1, 9)}",
            )
        planned.append(
            dict(
                s=s,
                cat=cat,
                sub=sub,
                title=title,
                description=description,
                block=block,
                room=room,
                created=created,
                status=status,
                closed_after=closed_after_days,
                feedback=feedback,
            )
        )

    # Personas first, so their ticket numbers never change (10019, 10024, ...).
    aarav, rohan, meera, kabir = (
        by_reg[r] for r in ("24100001", "24100003", "24100004", "24100005")
    )
    plan(aarav, "IT", "Wi-Fi", 0, _at(today - timedelta(days=2), 21, 10), "OPEN")
    plan(aarav, "HOSTEL", "Electrical", 0, _at(today - timedelta(days=9), 19, 40), "CLOSED", 3)
    plan(
        aarav,
        "LIBRARY",
        "Fine Waiver",
        0,
        _at(today - timedelta(days=30), 12, 5),
        "CLOSED",
        4,
        (True, 5),
    )
    plan(meera, "HOSTEL", "Plumbing", 0, _at(today - timedelta(days=3), 20, 15), "OPEN")
    plan(meera, "HOSTEL", "Plumbing", 1, _at(today - timedelta(days=1), 8, 50), "IN_PROGRESS")
    plan(
        meera,
        "IT",
        "UMS Login",
        0,
        _at(today - timedelta(days=12), 17, 30),
        "CLOSED",
        2,
        (False, 2),
    )
    plan(rohan, "FEE", "Payment Not Updated", 0, _at(today - timedelta(days=4), 11, 20), "OPEN")
    plan(
        kabir,
        "OTHER",
        "General Query",
        0,
        _at(today - timedelta(days=20), 10, 0),
        "CLOSED",
        1,
        (True, 4),
    )
    n_persona = len(planned)

    population = [s for s in students if s.persona is None]
    hostellers = [s for s in population if s.hostel]
    categories, weights = zip(*CATEGORY_WEIGHTS.items(), strict=True)
    for _ in range(max(20, len(population) // 3)):
        category = rng.choices(categories, weights=weights)[0]
        cat = rms.category(category)
        assert cat is not None
        s = rng.choice(hostellers if category == "HOSTEL" else population)
        sub = (
            cat.sub_categories[0]
            if category == "IT" and rng.random() < 0.5
            else rng.choice(cat.sub_categories)
        )
        age = rng.randint(1, 90)
        evening = category in ("HOSTEL", "IT") and rng.random() < 0.7
        created = _at(
            today - timedelta(days=age),
            rng.randint(18, 23) if evening else rng.randint(9, 17),
            rng.randint(0, 59),
        )
        if age > 14:
            status = "CLOSED" if rng.random() < 0.85 else "IN_PROGRESS"
        elif age > 4:
            status = rng.choices(["CLOSED", "IN_PROGRESS", "OPEN"], weights=[50, 30, 20])[0]
        else:
            status = rng.choices(["OPEN", "IN_PROGRESS"], weights=[60, 40])[0]
        closed_after = rng.randint(1, max(1, min(age - 1, 10))) if status == "CLOSED" else None
        feedback = None
        if status == "CLOSED" and rng.random() < 0.5:
            fixed = rng.random() < 0.85
            feedback = (fixed, rng.randint(4, 5) if fixed else rng.randint(1, 2))
        plan(s, category, sub, rng.randint(0, 5), created, status, closed_after, feedback)

    ordered = planned[:n_persona] + sorted(planned[n_persona:], key=lambda t: t["created"])
    persona_rng = random.Random("persona-tickets")
    for index, t in enumerate(ordered):
        number = ticket_number(1001 + index)
        r = persona_rng if index < n_persona else rng
        created = t["created"]
        events: list[tuple[str | None, str, str, str, datetime]] = [
            (None, "OPEN", "Request logged via web", "student", created)
        ]
        status, closed_at, feedback_at = t["status"], None, None
        if status != "OPEN":
            events.append(
                (
                    "OPEN",
                    "IN_PROGRESS",
                    "Assigned to the department",
                    "staff",
                    created + timedelta(hours=r.randint(2, 20)),
                )
            )
        remarks = None
        if status == "CLOSED":
            closed_at = created + timedelta(days=t["closed_after"], hours=r.randint(1, 6))
            remarks = r.choice(content.CLOSING_REMARKS)
            events.append(("IN_PROGRESS", "CLOSED", remarks, "staff", closed_at))
        resolved: bool | None = None
        rating: int | None = None
        if t["feedback"] is not None:
            assert closed_at is not None
            resolved, rating = t["feedback"]
            feedback_at = min(closed_at + timedelta(hours=r.randint(2, 30)), _at(today, 9))
            if not resolved:
                status = "REOPENED"
            events.append(
                (
                    "CLOSED",
                    status,
                    "Marked resolved" if resolved else "Not resolved; request reopened",
                    "student",
                    feedback_at,
                )
            )
        ds.add(
            "tickets",
            number=number,
            dept=t["cat"].dept,
            reg_no=t["s"].reg_no,
            category=t["cat"].id,
            sub_category=t["sub"],
            block=t["block"],
            room=t["room"],
            title=t["title"],
            description=t["description"],
            status=status,
            priority="NORMAL",
            channel="web",
            declaration_version=version,
            closing_remarks=remarks,
            closed_at=closed_at,
            feedback_resolved=resolved,
            feedback_rating=rating,
            feedback_comment=None,
            feedback_at=feedback_at,
            created_at=created,
            updated_at=events[-1][4],
        )
        for status_from, status_to, note, actor, at in events:
            ds.add(
                "ticket_events",
                ticket_number=number,
                status_from=status_from,
                status_to=status_to,
                note=note,
                actor=actor,
                at=at,
            )


def _hostel_leaves(ds: Dataset, rng: random.Random, students: list[_Student]) -> None:
    today = ds.today
    by_reg = {s.reg_no: s for s in students}
    ds.add(
        "hostel_leaves",
        reg_no="24100001",
        from_date=today - timedelta(days=24),
        to_date=today - timedelta(days=22),
        reason=content.LEAVE_REASONS[0],
        status="APPROVED",
        channel="web",
        created_at=_at(today - timedelta(days=28), 20),
    )
    ds.add(
        "hostel_leaves",
        reg_no="24100002",
        from_date=today + timedelta(days=6),
        to_date=today + timedelta(days=8),
        reason=content.LEAVE_REASONS[3],
        status="PENDING",
        channel="web",
        created_at=_at(today - timedelta(days=1), 21),
    )
    hostellers = [s for s in by_reg.values() if s.hostel and s.persona is None]
    for s in rng.sample(hostellers, k=min(len(hostellers), max(5, len(hostellers) // 8))):
        start = today + timedelta(days=rng.randint(-60, 20))
        status = (
            rng.choices(["APPROVED", "REJECTED"], weights=[85, 15])[0]
            if start < today
            else rng.choices(["PENDING", "APPROVED"], weights=[60, 40])[0]
        )
        ds.add(
            "hostel_leaves",
            reg_no=s.reg_no,
            from_date=start,
            to_date=start + timedelta(days=rng.randint(0, 4)),
            reason=rng.choice(content.LEAVE_REASONS),
            status=status,
            channel="web",
            created_at=_at(min(start, today) - timedelta(days=rng.randint(1, 6)), 20),
        )


def _content(ds: Dataset) -> None:
    today = ds.today
    for sort, (kind, title, body, menu_id) in enumerate(content.ANNOUNCEMENTS):
        ds.add("announcements", kind=kind, title=title, body=body, menu_id=menu_id, sort=sort)
    for offset, title, summary in content.NEWS:
        ds.add("news", title=title, summary=summary, published_on=today + timedelta(days=offset))
    for offset, hhmm, title, venue in content.EVENTS:
        hour, minute = map(int, hhmm.split(":"))
        ds.add(
            "events",
            title=title,
            venue=venue,
            starts_at=_at(today + timedelta(days=offset), hour, minute),
        )
    for i, (company, role, lpa, programmes, min_cgpa, register_in) in enumerate(content.DRIVES, 1):
        register_by = today + timedelta(days=register_in)
        ds.add(
            "placement_drives",
            id=i,
            company=company,
            role=role,
            package_lpa=Decimal(str(lpa)),
            drive_date=register_by + timedelta(days=7),
            register_by=register_by,
            programmes=programmes,
            min_cgpa=Decimal(str(min_cgpa)),
        )


# --- sanity statistics (used by tests and `python -m mini_ums_api.seed --stats`) -------------


def stats(ds: Dataset) -> dict[str, float]:
    threshold = conventions().policies.attendance_min_percent / 100
    attendance = ds.rows("attendance")
    per_student: dict[str, list[tuple[int, int]]] = {}
    for a in attendance:
        per_student.setdefault(a["reg_no"], []).append((a["attended"], a["held"]))
    below_overall = sum(
        sum(x for x, _ in v) / sum(h for _, h in v) < threshold for v in per_student.values()
    )
    any_course_below = sum(any(x / h < threshold for x, h in v) for v in per_student.values())
    overdue = {
        f["reg_no"] for f in ds.rows("fees") if f["paid"] < f["amount"] and f["due_date"] < ds.today
    }
    enrolments = {(a["reg_no"], a["course_code"]) for a in attendance}
    with_marks = {(m["reg_no"], m["course_code"]) for m in ds.rows("marks")}
    tickets = ds.rows("tickets")
    n = len(per_student)
    return {
        "students": n,
        "share_below_threshold_overall": below_overall / n,
        "share_with_a_course_below_threshold": any_course_below / n,
        "share_with_overdue_fees": len(overdue) / n,
        "share_enrolments_without_marks": 1 - len(with_marks & enrolments) / len(enrolments),
        "tickets": len(tickets),
        "share_tickets_hostel_or_it": sum(t["category"] in ("HOSTEL", "IT") for t in tickets)
        / len(tickets),
        "share_tickets_open": sum(t["status"] != "CLOSED" for t in tickets) / len(tickets),
    }
