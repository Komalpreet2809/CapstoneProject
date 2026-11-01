"""Request and response models: the API contract.

Request models forbid unknown fields, so a body can never smuggle in a `student_id`: the
student always comes from the session token (rule 1).
"""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mini_ums_api.conventions import conventions

Channel = Literal["web", "voice"]
TicketStatus = Literal["OPEN", "IN_PROGRESS", "CLOSED", "REOPENED"]
LeaveStatus = Literal["PENDING", "APPROVED", "REJECTED", "CANCELLED"]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- auth & profile -------------------------------------------------------------------------


class LoginIn(_In):
    reg_no: str = Field(pattern=str(conventions().ids["reg_no"]["pattern"]))
    password: str = Field(min_length=1, max_length=128)


class StudentProfile(_Out):
    reg_no: str
    vid: str
    name: str
    programme_code: str
    programme: str
    school: str
    section: str
    term: str
    cgpa: float | None
    is_hosteller: bool
    hostel_block: str | None
    room: str | None
    preferred_language: str
    password_expires_in_days: int


class LoginOut(_Out):
    token: str
    expires_at: datetime
    student: StudentProfile


# --- academics ------------------------------------------------------------------------------


class AttendanceOut(_Out):
    course_code: str
    course_title: str
    held: int
    attended: int
    percent: float | None = Field(description="Null when no classes have been held yet")
    threshold: float
    meets_threshold: bool | None
    classes_needed: int = Field(description="Consecutive classes to attend to reach threshold")
    can_miss: int = Field(description="Classes that can be missed while staying at threshold")
    last_updated: datetime


class CourseOut(_Out):
    code: str
    title: str
    credits: int
    kind: str
    term: str
    faculty: str
    roll_no: str
    group_no: int
    attendance: AttendanceOut


class TimetableEntry(_Out):
    start: time
    end: time
    course_code: str
    course_title: str
    room: str
    kind: str
    mandatory: bool


class TimetableOut(_Out):
    date: date
    weekday: str
    entries: list[TimetableEntry]


class FeeItem(_Out):
    head: str
    amount: float
    paid: float
    due: float
    due_date: date
    overdue: bool


class FeesOut(_Out):
    currency: Literal["INR"] = "INR"
    items: list[FeeItem]
    total_due: float
    overdue_due: float


class Seat(_Out):
    building: str
    room: str
    seat: str


class ExamOut(_Out):
    course_code: str
    course_title: str
    exam_type: str
    date: date
    start: time
    end: time
    seating: Seat | None


class AssignmentOut(_Out):
    id: int
    course_code: str
    course_title: str
    title: str
    kind: str
    last_date: date
    max_marks: int
    submitted: bool
    submitted_at: datetime | None
    days_left: int


# --- content --------------------------------------------------------------------------------


class AnnouncementOut(_Out):
    id: int
    kind: Literal["ribbon", "banner"]
    title: str
    body: str
    menu_id: str | None


class NewsOut(_Out):
    id: int
    title: str
    summary: str
    published_on: date


class EventOut(_Out):
    id: int
    title: str
    venue: str
    starts_at: datetime


class MessageOut(_Out):
    id: int
    sender_name: str
    sender_role: str
    subject: str
    body: str
    sent_at: datetime


class PlacementDriveOut(_Out):
    id: int
    company: str
    role: str
    package_lpa: float
    drive_date: date
    register_by: date
    read: bool


class DriveAckIn(_In):
    drive_ids: list[int] = Field(min_length=1, max_length=50)
    action: Literal["read", "later"]


# --- RMS ------------------------------------------------------------------------------------


class TicketCreate(_In):
    category: str
    sub_category: str
    block: str | None = Field(default=None, max_length=20)
    room: str | None = Field(default=None, max_length=20)
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=500)
    declaration_version: str
    allow_duplicate: bool = False
    channel: Channel = "web"

    @model_validator(mode="after")
    def _check_against_conventions(self) -> "TicketCreate":
        rms = conventions().rms
        category = rms.category(self.category)
        if category is None:
            raise ValueError(f"unknown category {self.category!r}")
        if self.sub_category not in category.sub_categories:
            raise ValueError(f"unknown sub-category {self.sub_category!r} for {category.id}")
        if category.needs_location and not (self.block and self.room):
            raise ValueError(f"{category.label} requests need a block and room")
        if self.declaration_version != rms.declarations.version:
            raise ValueError("declarations must be accepted (current version required)")
        return self


class Feedback(_Out):
    resolved: bool
    rating: int
    comment: str | None
    at: datetime


class TicketOut(_Out):
    number: str = Field(description="5-digit ticket number (4-digit sequence + check digit)")
    request_id: str = Field(description="UMS-style display ID: DEPT/Mon-YY/NNNNN")
    speakable: str = Field(description="Number spaced digit by digit, for text-to-speech")
    dept: str
    category: str
    category_label: str
    sub_category: str
    block: str | None
    room: str | None
    title: str
    description: str
    status: TicketStatus
    priority: Literal["NORMAL", "HIGH"]
    channel: Channel
    created_at: datetime
    updated_at: datetime
    closing_remarks: str | None
    closed_at: datetime | None
    feedback: Feedback | None
    can_give_feedback: bool


class TicketEventOut(_Out):
    status_from: str | None
    status_to: str
    note: str | None
    actor: Literal["student", "staff", "system"]
    at: datetime


class TicketDetailOut(TicketOut):
    events: list[TicketEventOut]


class TicketCounts(_Out):
    total: int
    open: int
    closed: int


class TicketHistoryOut(_Out):
    counts: TicketCounts
    tickets: list[TicketOut]


class DuplicateTicketOut(_Out):
    detail: str
    similar: TicketOut


class NoteIn(_In):
    note: str = Field(min_length=3, max_length=500)


class FeedbackIn(_In):
    resolved: bool
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)


# --- hostel leave ---------------------------------------------------------------------------


class LeaveCreate(_In):
    from_date: date
    to_date: date
    reason: str = Field(min_length=5, max_length=300)
    channel: Channel = "web"

    @model_validator(mode="after")
    def _ordered(self) -> "LeaveCreate":
        if self.to_date < self.from_date:
            raise ValueError("to_date must be on or after from_date")
        return self


class LeaveOut(_Out):
    id: int
    from_date: date
    to_date: date
    days: int
    reason: str
    status: LeaveStatus
    channel: Channel
    created_at: datetime


class ErrorOut(BaseModel):
    detail: str
