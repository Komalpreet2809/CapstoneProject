-- Mini UMS schema. Synthetic data only.
-- Computed values (attendance %, dues, ticket counts) are derived in code, not stored.

CREATE TABLE programmes (
  code   TEXT PRIMARY KEY,
  name   TEXT NOT NULL,
  school TEXT NOT NULL
);

CREATE TABLE students (
  reg_no              TEXT PRIMARY KEY,
  vid                 TEXT NOT NULL UNIQUE,
  name                TEXT NOT NULL,
  programme_code      TEXT NOT NULL REFERENCES programmes (code),
  section             TEXT NOT NULL,
  term                TEXT NOT NULL,
  cgpa                NUMERIC(4, 2),
  is_hosteller        BOOLEAN NOT NULL,
  hostel_block        TEXT,
  room                TEXT,
  phone_mock          TEXT NOT NULL,
  email_mock          TEXT NOT NULL,
  preferred_language  TEXT NOT NULL DEFAULT 'en',
  password_hash       TEXT NOT NULL,
  password_changed_at TIMESTAMPTZ NOT NULL,
  failed_logins       INT NOT NULL DEFAULT 0,
  locked_until        TIMESTAMPTZ,
  is_demo             BOOLEAN NOT NULL DEFAULT false,
  CHECK (is_hosteller = (hostel_block IS NOT NULL))
);
CREATE INDEX students_section_idx ON students (section);

CREATE TABLE sessions (
  token_hash TEXT PRIMARY KEY,
  reg_no     TEXT NOT NULL REFERENCES students (reg_no) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE faculty (
  id   TEXT PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE courses (
  code    TEXT PRIMARY KEY,
  title   TEXT NOT NULL,
  credits INT NOT NULL,
  kind    TEXT NOT NULL CHECK (kind IN ('Theory', 'Practical', 'Project'))
);

CREATE TABLE enrollments (
  reg_no      TEXT NOT NULL REFERENCES students (reg_no) ON DELETE CASCADE,
  course_code TEXT NOT NULL REFERENCES courses (code),
  term        TEXT NOT NULL,
  faculty_id  TEXT NOT NULL REFERENCES faculty (id),
  roll_no     TEXT NOT NULL,
  group_no    INT NOT NULL,
  PRIMARY KEY (reg_no, course_code, term)
);

CREATE TABLE attendance (
  reg_no       TEXT NOT NULL,
  course_code  TEXT NOT NULL,
  term         TEXT NOT NULL,
  held         INT NOT NULL CHECK (held >= 0),
  attended     INT NOT NULL CHECK (attended >= 0),
  last_updated TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (reg_no, course_code, term),
  FOREIGN KEY (reg_no, course_code, term) REFERENCES enrollments ON DELETE CASCADE,
  CHECK (attended <= held)
);

CREATE TABLE marks (
  reg_no      TEXT NOT NULL,
  course_code TEXT NOT NULL,
  term        TEXT NOT NULL,
  component   TEXT NOT NULL,
  score       NUMERIC(5, 2) NOT NULL,
  max_score   NUMERIC(5, 2) NOT NULL,
  PRIMARY KEY (reg_no, course_code, term, component),
  FOREIGN KEY (reg_no, course_code, term) REFERENCES enrollments ON DELETE CASCADE,
  CHECK (score BETWEEN 0 AND max_score)
);

CREATE TABLE timetable (
  id          SERIAL PRIMARY KEY,
  section     TEXT NOT NULL,
  day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
  start_time  TIME NOT NULL,
  end_time    TIME NOT NULL,
  course_code TEXT NOT NULL REFERENCES courses (code),
  room        TEXT NOT NULL,
  kind        TEXT NOT NULL CHECK (kind IN ('Lecture', 'Tutorial', 'Practical')),
  mandatory   BOOLEAN NOT NULL DEFAULT false,
  CHECK (start_time < end_time)
);
CREATE INDEX timetable_section_day_idx ON timetable (section, day_of_week);

CREATE TABLE fees (
  id       SERIAL PRIMARY KEY,
  reg_no   TEXT NOT NULL REFERENCES students (reg_no) ON DELETE CASCADE,
  head     TEXT NOT NULL,
  amount   NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
  paid     NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (paid >= 0),
  due_date DATE NOT NULL,
  CHECK (paid <= amount)
);
CREATE INDEX fees_reg_no_idx ON fees (reg_no);

CREATE TABLE assignments (
  id          SERIAL PRIMARY KEY,
  course_code TEXT NOT NULL REFERENCES courses (code),
  section     TEXT NOT NULL,
  term        TEXT NOT NULL,
  title       TEXT NOT NULL,
  kind        TEXT NOT NULL,
  last_date   DATE NOT NULL,
  max_marks   INT NOT NULL
);
CREATE INDEX assignments_section_idx ON assignments (section);

CREATE TABLE submissions (
  assignment_id INT NOT NULL REFERENCES assignments (id) ON DELETE CASCADE,
  reg_no        TEXT NOT NULL REFERENCES students (reg_no) ON DELETE CASCADE,
  submitted_at  TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (assignment_id, reg_no)
);

CREATE TABLE exams (
  id          SERIAL PRIMARY KEY,
  course_code TEXT NOT NULL REFERENCES courses (code),
  term        TEXT NOT NULL,
  exam_type   TEXT NOT NULL,
  exam_date   DATE NOT NULL,
  start_time  TIME NOT NULL,
  end_time    TIME NOT NULL,
  UNIQUE (course_code, term, exam_type)
);

CREATE TABLE seating (
  exam_id  INT NOT NULL REFERENCES exams (id) ON DELETE CASCADE,
  reg_no   TEXT NOT NULL REFERENCES students (reg_no) ON DELETE CASCADE,
  building TEXT NOT NULL,
  room     TEXT NOT NULL,
  seat     TEXT NOT NULL,
  PRIMARY KEY (exam_id, reg_no)
);

-- Ticket numbers: 4-digit sequence + Damm check digit, assigned in code (ids.py).
CREATE SEQUENCE ticket_seq START 1001 MINVALUE 1001 MAXVALUE 9999;

CREATE TABLE tickets (
  number              TEXT PRIMARY KEY CHECK (number ~ '^[0-9]{5}$'),
  dept                TEXT NOT NULL,
  reg_no              TEXT NOT NULL REFERENCES students (reg_no) ON DELETE CASCADE,
  category            TEXT NOT NULL,
  sub_category        TEXT NOT NULL,
  block               TEXT,
  room                TEXT,
  title               TEXT NOT NULL,
  description         TEXT NOT NULL,
  status              TEXT NOT NULL DEFAULT 'OPEN'
                      CHECK (status IN ('OPEN', 'IN_PROGRESS', 'CLOSED', 'REOPENED')),
  priority            TEXT NOT NULL DEFAULT 'NORMAL' CHECK (priority IN ('NORMAL', 'HIGH')),
  channel             TEXT NOT NULL DEFAULT 'web' CHECK (channel IN ('web', 'voice')),
  declaration_version TEXT NOT NULL,
  closing_remarks     TEXT,
  closed_at           TIMESTAMPTZ,
  feedback_resolved   BOOLEAN,
  feedback_rating     SMALLINT CHECK (feedback_rating BETWEEN 1 AND 5),
  feedback_comment    TEXT,
  feedback_at         TIMESTAMPTZ,
  idempotency_key     TEXT UNIQUE,
  request_hash        TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX tickets_reg_no_created_idx ON tickets (reg_no, created_at DESC);

CREATE TABLE ticket_events (
  id            BIGSERIAL PRIMARY KEY,
  ticket_number TEXT NOT NULL REFERENCES tickets (number) ON DELETE CASCADE,
  status_from   TEXT,
  status_to     TEXT NOT NULL,
  note          TEXT,
  actor         TEXT NOT NULL CHECK (actor IN ('student', 'staff', 'system')),
  at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ticket_events_ticket_idx ON ticket_events (ticket_number, at);

CREATE TABLE hostel_leaves (
  id              SERIAL PRIMARY KEY,
  reg_no          TEXT NOT NULL REFERENCES students (reg_no) ON DELETE CASCADE,
  from_date       DATE NOT NULL,
  to_date         DATE NOT NULL,
  reason          TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'PENDING'
                  CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')),
  channel         TEXT NOT NULL DEFAULT 'web' CHECK (channel IN ('web', 'voice')),
  idempotency_key TEXT UNIQUE,
  request_hash    TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (from_date <= to_date)
);
CREATE INDEX hostel_leaves_reg_no_idx ON hostel_leaves (reg_no, created_at DESC);

CREATE TABLE announcements (
  id      SERIAL PRIMARY KEY,
  kind    TEXT NOT NULL CHECK (kind IN ('ribbon', 'banner')),
  title   TEXT NOT NULL,
  body    TEXT NOT NULL,
  menu_id TEXT,
  sort    INT NOT NULL DEFAULT 0
);

CREATE TABLE news (
  id           SERIAL PRIMARY KEY,
  title        TEXT NOT NULL,
  summary      TEXT NOT NULL,
  published_on DATE NOT NULL
);

CREATE TABLE events (
  id        SERIAL PRIMARY KEY,
  title     TEXT NOT NULL,
  venue     TEXT NOT NULL,
  starts_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE messages (
  id          SERIAL PRIMARY KEY,
  section     TEXT NOT NULL,
  sender_name TEXT NOT NULL,
  sender_role TEXT NOT NULL,
  subject     TEXT NOT NULL,
  body        TEXT NOT NULL,
  sent_at     TIMESTAMPTZ NOT NULL
);
CREATE INDEX messages_section_idx ON messages (section, sent_at DESC);

CREATE TABLE placement_drives (
  id          SERIAL PRIMARY KEY,
  company     TEXT NOT NULL,
  role        TEXT NOT NULL,
  package_lpa NUMERIC(5, 2) NOT NULL,
  drive_date  DATE NOT NULL,
  register_by DATE NOT NULL,
  programmes  TEXT[] NOT NULL,
  min_cgpa    NUMERIC(4, 2) NOT NULL
);

CREATE TABLE drive_acks (
  reg_no       TEXT NOT NULL REFERENCES students (reg_no) ON DELETE CASCADE,
  drive_id     INT NOT NULL REFERENCES placement_drives (id) ON DELETE CASCADE,
  read_at      TIMESTAMPTZ,
  remind_after TIMESTAMPTZ,
  PRIMARY KEY (reg_no, drive_id)
);
