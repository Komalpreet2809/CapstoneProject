// Shapes returned by the Mini UMS API (apps/mini_ums_api/src/mini_ums_api/schemas.py).
// Dates arrive as ISO strings.

export type StudentProfile = {
  reg_no: string;
  vid: string;
  name: string;
  programme_code: string;
  programme: string;
  school: string;
  section: string;
  term: string;
  cgpa: number | null;
  is_hosteller: boolean;
  hostel_block: string | null;
  room: string | null;
  preferred_language: string;
  password_expires_in_days: number;
};

export type LoginOut = { token: string; expires_at: string; student: StudentProfile };

export type DemoAccount = { reg_no: string; name: string; password: string; scenario: string };

export type Attendance = {
  course_code: string;
  course_title: string;
  held: number;
  attended: number;
  percent: number | null;
  threshold: number;
  meets_threshold: boolean | null;
  classes_needed: number;
  can_miss: number;
  last_updated: string;
};

export type Course = {
  code: string;
  title: string;
  credits: number;
  kind: string;
  term: string;
  faculty: string;
  roll_no: string;
  group_no: number;
  attendance: Attendance;
};

export type FeeItem = {
  head: string;
  amount: number;
  paid: number;
  due: number;
  due_date: string;
  overdue: boolean;
};

export type Fees = { currency: "INR"; items: FeeItem[]; total_due: number; overdue_due: number };

export type Assignment = {
  id: number;
  course_code: string;
  course_title: string;
  title: string;
  kind: string;
  last_date: string;
  max_marks: number;
  submitted: boolean;
  submitted_at: string | null;
  days_left: number;
};

export type Announcement = {
  id: number;
  kind: "ribbon" | "banner";
  title: string;
  body: string;
  menu_id: string | null;
};

export type News = { id: number; title: string; summary: string; published_on: string };

export type CampusEvent = { id: number; title: string; venue: string; starts_at: string };

export type Message = {
  id: number;
  sender_name: string;
  sender_role: string;
  subject: string;
  body: string;
  sent_at: string;
};

export type PlacementDrive = {
  id: number;
  company: string;
  role: string;
  package_lpa: number;
  drive_date: string;
  register_by: string;
  read: boolean;
};

export type MenuEntry = { id: string; label: string; route: string | null; keywords: string[] };
export type MenuGroup = { label: string; entries: MenuEntry[] };
export type Menu = { id: string; label: string; groups: MenuGroup[] };
export type MenuCatalogue = { menu: Menu[]; sidebar: string[]; shortcuts: string[] };

export type RmsCategory = {
  id: string;
  label: string;
  dept: string;
  needs_location: boolean;
  sub_categories: string[];
};

export type RmsCatalogue = {
  declarations: { version: string; items: string[] };
  categories: RmsCategory[];
};

export type TicketStatus = "OPEN" | "IN_PROGRESS" | "CLOSED" | "REOPENED";

export type Ticket = {
  number: string;
  request_id: string;
  speakable: string;
  dept: string;
  category: string;
  category_label: string;
  sub_category: string;
  block: string | null;
  room: string | null;
  title: string;
  description: string;
  status: TicketStatus;
  priority: "NORMAL" | "HIGH";
  channel: "web" | "voice";
  created_at: string;
  updated_at: string;
  closing_remarks: string | null;
  closed_at: string | null;
  feedback: { resolved: boolean; rating: number; comment: string | null; at: string } | null;
  can_give_feedback: boolean;
};

export type TicketEvent = {
  status_from: string | null;
  status_to: string;
  note: string | null;
  actor: "student" | "staff" | "system";
  at: string;
};

export type TicketDetail = Ticket & { events: TicketEvent[] };

export type TicketHistory = {
  counts: { total: number; open: number; closed: number };
  tickets: Ticket[];
};

export type DuplicateTicket = { detail: string; similar: Ticket };
