"""Stable demo personas: same data on every re-seed, whatever the population seed or size.

Each persona exists to demonstrate specific behaviour; `scenario` says which. The password is
shown on the login page only when ENVIRONMENT=dev.
"""

from dataclasses import dataclass
from typing import Literal

PERSONA_PASSWORD = "Demo@1234"


@dataclass(frozen=True)
class Persona:
    reg_no: str
    name: str
    gender: Literal["M", "F"]
    programme: str
    section_no: int
    hostel: tuple[str, str] | None  # (block, room)
    cgpa: float
    language: str
    scenario: str
    password_age_days: int
    attendance: tuple[float, ...]  # target ratio per course, in course order
    fees: Literal["clear", "due_soon", "overdue"]
    locked: bool = False


PERSONAS: tuple[Persona, ...] = (
    Persona(
        reg_no="24100001",
        name="Aarav Mehta",
        gender="M",
        programme="CS",
        section_no=1,
        hostel=("BH-3", "412"),
        cgpa=8.1,
        language="en",
        scenario="Hosteller; one course below 75%; hostel fee due soon; open Wi-Fi request and "
        "a closed request awaiting feedback",
        password_age_days=50,
        attendance=(0.88, 0.82, 0.72, 0.91, 0.79, 0.85, 0.90),
        fees="due_soon",
    ),
    Persona(
        reg_no="24100002",
        name="Simran Kaur",
        gender="F",
        programme="CS",
        section_no=1,
        hostel=("GH-2", "118"),
        cgpa=9.1,
        language="pa",
        scenario="Punjabi speaker; all attendance above 85%; fees NIL; password expires in 5 days",
        password_age_days=85,
        attendance=(0.92, 0.89, 0.95, 0.87, 0.91, 0.93, 0.88),
        fees="clear",
    ),
    Persona(
        reg_no="24100003",
        name="Rohan Verma",
        gender="M",
        programme="ME",
        section_no=1,
        hostel=None,
        cgpa=6.3,
        language="hi",
        scenario="Day scholar (no hostel leave); several courses below 75%; overdue tuition fee; "
        "open fee request",
        password_age_days=20,
        attendance=(0.62, 0.71, 0.74, 0.68, 0.80, 0.66, 0.77),
        fees="overdue",
    ),
    Persona(
        reg_no="24100004",
        name="Meera Iyer",
        gender="F",
        programme="EC",
        section_no=1,
        hostel=("GH-1", "207"),
        cgpa=7.6,
        language="en",
        scenario="Two open plumbing requests (duplicate check); a reopened request; one course "
        "exactly at 75.00%",
        password_age_days=10,
        attendance=(0.81, 0.84, 0.75, 0.86, 0.79, 0.83, 0.88),
        fees="due_soon",
    ),
    Persona(
        reg_no="24100005",
        name="Kabir Singh",
        gender="M",
        programme="BB",
        section_no=1,
        hostel=None,
        cgpa=7.0,
        language="hi",
        scenario="Locked account: every login is refused",
        password_age_days=30,
        attendance=(0.80, 0.78, 0.82, 0.76, 0.85, 0.79, 0.81),
        fees="clear",
        locked=True,
    ),
    Persona(
        reg_no="24100006",
        name="Ananya Gupta",
        gender="F",
        programme="BS",
        section_no=1,
        hostel=("GH-3", "210"),
        cgpa=7.9,
        language="en",
        scenario="Classmate with a near-identical name (Anaya Gupta); no requests yet",
        password_age_days=30,
        attendance=(0.84, 0.77, 0.90, 0.73, 0.86, 0.81, 0.88),
        fees="clear",
    ),
)

# Edge case: a population student in Ananya's section with a near-identical name.
SIMILAR_NAME = ("Anaya Gupta", "F", "BS", 1)
