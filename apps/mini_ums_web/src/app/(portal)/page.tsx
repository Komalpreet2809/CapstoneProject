import Link from "next/link";
import { Suspense } from "react";
import { AttendanceRing } from "@/components/dashboard/AttendanceRing";
import { BannerCarousel } from "@/components/dashboard/BannerCarousel";
import { Card, CardSkeleton, EmptyState } from "@/components/dashboard/Card";
import { PlacementDriveDialog } from "@/components/dashboard/PlacementDriveDialog";
import { Icon } from "@/components/icons";
import {
  getAnnouncements,
  getCourses,
  getEvents,
  getFees,
  getMenu,
  getMessages,
  getNews,
  getPendingAssignments,
  getPendingDrives,
  getPlacementDrives,
  getProfile,
} from "@/lib/data";
import {
  dayAndMonth,
  dmyInDays,
  dueIn,
  formatDate,
  formatDmy,
  formatInr,
  formatTime,
  initials,
} from "@/lib/format";
import { entriesById, entryHref } from "@/lib/menu";

const PASSWORD_WARNING_DAYS = 10;

// Pill text for the "Important Links" row, where the menu label is too long.
const PILL_LABELS: Record<string, string> = {
  "rms-log-request": "RMS",
  "academic-certificate": "Certificate Request",
  "part-time-jobs": "Part-time Job",
  "exam-date-sheet": "Exam Date Sheet",
  "placement-drives": "Placement Portal",
  "emergency-numbers": "Emergency Numbers",
  "academic-calendar": "Academic Calendar",
};

/** Section order and card set follow the real portal's dashboard (docs/reference). */
export default function Dashboard() {
  return (
    <div className="mx-auto max-w-[96rem] space-y-5">
      <Suspense fallback={<div className="h-5" />}>
        <PasswordNotice />
      </Suspense>

      <section aria-labelledby="important-links">
        <h1 id="important-links" className="text-2xl font-semibold text-stone-900">
          Important Links
        </h1>
        <Suspense fallback={<div className="mt-3 h-9 animate-pulse rounded-full bg-stone-200" />}>
          <ImportantLinks />
        </Suspense>
      </section>

      <div className="grid gap-x-5 gap-y-4 lg:grid-cols-2 2xl:grid-cols-4">
        <div className="mt-4 lg:col-span-2">
          <Suspense fallback={<div className="h-full min-h-52 animate-pulse rounded-2xl bg-stone-200" />}>
            <Banners />
          </Suspense>
        </div>
        <Suspense fallback={<CardSkeleton />}>
          <Happening />
        </Suspense>
        <Suspense fallback={<CardSkeleton />}>
          <Messages />
        </Suspense>
      </div>

      <div className="grid gap-x-5 gap-y-4 md:grid-cols-2 2xl:grid-cols-4">
        <Suspense fallback={<CardSkeleton rows={5} />}>
          <MyCourses />
        </Suspense>
        <Suspense fallback={<CardSkeleton rows={2} />}>
          <FeeCard />
        </Suspense>
        <Suspense fallback={<CardSkeleton />}>
          <PendingAssignments />
        </Suspense>
        <Suspense fallback={<CardSkeleton />}>
          <Events />
        </Suspense>
      </div>

      <Suspense fallback={<CardSkeleton rows={3} />}>
        <PlacementDetails />
      </Suspense>

      <Suspense fallback={null}>
        <CampusDriveNotifications />
      </Suspense>
    </div>
  );
}

async function PasswordNotice() {
  const p = await getProfile();
  const days = p.password_expires_in_days;
  const by = dmyInDays(Math.max(days, 0));
  if (days > PASSWORD_WARNING_DAYS) {
    return (
      <p className="text-right text-xs text-stone-500">
        Your password will expire after {days} days. Change it on or before {by}.
      </p>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl bg-marigold-50 px-4 py-3 text-sm text-stone-800 ring-1 ring-marigold-200">
      <Icon name="lock" className="size-5 text-marigold-500" />
      <span className="flex-1">
        {days > 0 ? (
          <>
            Your password expires in <strong>{days === 1 ? "1 day" : `${days} days`}</strong>.
            Change it on or before <strong>{by}</strong>.
          </>
        ) : (
          <strong>Your password has expired. Change it to keep using the portal.</strong>
        )}
      </span>
      <Link
        href="/m/change-password"
        className="rounded-lg bg-brand-700 px-3 py-1.5 font-semibold text-white hover:bg-brand-800"
      >
        Change password
      </Link>
    </div>
  );
}

async function ImportantLinks() {
  const catalogue = await getMenu();
  return (
    <nav aria-labelledby="important-links" className="mt-3 flex flex-wrap gap-2">
      {entriesById(catalogue, catalogue.shortcuts).map((entry, i) => (
        <Link
          key={entry.id}
          href={entryHref(entry)}
          className={`rounded-full px-4 py-1.5 text-sm font-semibold shadow-sm transition ${
            i === 0
              ? "bg-marigold-400 text-brand-950 hover:bg-marigold-300"
              : "bg-brand-700 text-white hover:bg-brand-800"
          }`}
        >
          {PILL_LABELS[entry.id] ?? entry.label}
        </Link>
      ))}
    </nav>
  );
}

async function Banners() {
  const banners = (await getAnnouncements()).filter((a) => a.kind === "banner");
  if (banners.length === 0) return null;
  return (
    <BannerCarousel
      slides={banners.map((b) => ({
        id: b.id,
        title: b.title,
        body: b.body,
        href: b.menu_id ? `/m/${b.menu_id}` : null,
      }))}
    />
  );
}

async function Happening() {
  const news = await getNews();
  return (
    <Card
      title="Happening"
      icon="sparkle"
      note="* Happening on campus"
      actions={[{ href: "/m/happening", label: "View More" }]}
    >
      <ul className="max-h-72 divide-y divide-stone-100 overflow-y-auto pr-1">
        {news.map((n) => (
          <li key={n.id} className="py-2.5 first:pt-0">
            <p className="text-sm font-semibold text-stone-800">{n.title}</p>
            <p className="line-clamp-2 text-xs text-stone-600">{n.summary}</p>
            <p className="mt-0.5 text-[11px] text-brand-700">{formatDate(n.published_on)}</p>
          </li>
        ))}
      </ul>
    </Card>
  );
}

async function Messages() {
  const messages = await getMessages();
  return (
    <Card
      title="My Messages"
      icon="mail"
      note="* Messages sent by teachers"
      actions={[{ href: "/m/messages", label: "All Messages" }]}
    >
      {messages.length === 0 ? (
        <EmptyState icon="mail">No messages yet.</EmptyState>
      ) : (
        <ul className="max-h-72 space-y-3 overflow-y-auto pr-1">
          {messages.map((m) => (
            <li key={m.id} className="flex gap-2">
              <span className="mt-1.5 size-2 shrink-0 rounded-full ring-2 ring-brand-600" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-stone-800">
                  {m.subject} - By {m.sender_name}{" "}
                  <span className="font-normal text-stone-500">({formatDate(m.sent_at)})</span>
                </p>
                <p className="line-clamp-3 text-xs text-stone-500">{m.body}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

async function MyCourses() {
  const [courses, profile] = await Promise.all([getCourses(), getProfile()]);
  const held = courses.reduce((sum, c) => sum + c.attendance.held, 0);
  const attended = courses.reduce((sum, c) => sum + c.attendance.attended, 0);
  const overall = held > 0 ? Math.round((attended / held) * 100) : null;
  return (
    <Card
      title="My Courses"
      icon="book"
      note={
        <span className="font-semibold text-stone-700">
          CGPA : {profile.cgpa?.toFixed(2) ?? "–"} · ATTENDANCE : {overall ?? "–"}%
        </span>
      }
    >
      {courses.length === 0 ? (
        <EmptyState icon="book">No courses registered this term.</EmptyState>
      ) : (
        <ul className="max-h-96 divide-y divide-stone-100 overflow-y-auto pr-1">
          {courses.map((c) => {
            const a = c.attendance;
            return (
              <li key={c.code} className="flex gap-3 py-3 first:pt-0">
                <AttendanceRing percent={a.percent} threshold={a.threshold} />
                <div className="min-w-0 text-xs text-stone-600">
                  <p className="text-sm font-semibold text-stone-800">
                    {c.code} : {c.title}
                  </p>
                  <p>Term : {c.term}</p>
                  <p>
                    Roll No : {c.roll_no} / Group {c.group_no}
                  </p>
                  <AttendanceHint
                    percent={a.percent}
                    meets={a.meets_threshold}
                    needed={a.classes_needed}
                    canMiss={a.can_miss}
                    threshold={a.threshold}
                  />
                  <p className="mt-1 flex flex-wrap gap-x-2.5 font-medium text-brand-700">
                    <Link href="/m/instruction-plan" className="hover:underline">
                      IP
                    </Link>
                    <Link href="/m/syllabus" className="hover:underline">
                      Syllabus
                    </Link>
                    <Link href="/m/time-table" className="hover:underline">
                      Timetable
                    </Link>
                    <Link href="/m/student-attendance" className="hover:underline">
                      Attendance
                    </Link>
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

function AttendanceHint(props: {
  percent: number | null;
  meets: boolean | null;
  needed: number;
  canMiss: number;
  threshold: number;
}) {
  if (props.percent === null) return <p>No classes yet</p>;
  if (!props.meets) {
    return (
      <p className="font-medium text-rose-700">
        Attend the next {props.needed} to reach {props.threshold}%
      </p>
    );
  }
  return (
    <p>
      {props.canMiss === 0
        ? "Don’t miss the next class"
        : `Can miss ${props.canMiss} class${props.canMiss === 1 ? "" : "es"}`}
    </p>
  );
}

async function FeeCard() {
  const fees = await getFees();
  const unpaid = fees.items.filter((f) => f.due > 0);
  return (
    <Card
      title="Fee"
      icon="wallet"
      actions={[
        { href: "/m/fee-schedule", label: "Fee Notification" },
        { href: "/m/online-transactions", label: "Transactions" },
      ]}
    >
      {fees.total_due === 0 ? (
        <p className="py-6 text-center text-4xl font-bold tracking-wide text-brand-800">NIL</p>
      ) : (
        <>
          <p className="text-sm text-stone-500">Total due</p>
          <p className="text-3xl font-bold text-stone-900">{formatInr(fees.total_due)}</p>
          {fees.overdue_due > 0 && (
            <p className="mt-1 inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-200">
              <Icon name="alert" className="size-3.5" />
              {formatInr(fees.overdue_due)} overdue
            </p>
          )}
          <ul className="mt-3 divide-y divide-stone-100 text-sm">
            {unpaid.map((f) => (
              <li key={f.head} className="flex items-center justify-between gap-3 py-2">
                <div>
                  <p className="font-medium text-stone-800">{f.head}</p>
                  <p className={`text-xs ${f.overdue ? "text-rose-700" : "text-stone-500"}`}>
                    {f.overdue ? "Was due" : "Due"} {formatDmy(f.due_date)}
                  </p>
                </div>
                <span className="font-semibold text-stone-800">{formatInr(f.due)}</span>
              </li>
            ))}
          </ul>
          <Link
            href="/m/fee-dashboard"
            className="mt-3 block rounded-lg bg-marigold-400 py-2 text-center text-sm font-semibold text-brand-950 hover:bg-marigold-300"
          >
            Pay fee
          </Link>
        </>
      )}
    </Card>
  );
}

async function PendingAssignments() {
  const items = (await getPendingAssignments()).sort((a, b) => a.days_left - b.days_left);
  return (
    <Card
      title="Pending Assignments"
      icon="clipboard"
      actions={[
        { href: "/m/assignment-upload", label: "Upload" },
        { href: "/m/pending-assignments", label: "View Assignments" },
      ]}
    >
      {items.length === 0 ? (
        <EmptyState icon="check">Nothing pending. Nice work!</EmptyState>
      ) : (
        <ul className="max-h-80 divide-y divide-stone-100 overflow-y-auto pr-1">
          {items.map((a) => (
            <li key={a.id} className="py-2.5 first:pt-0">
              <p className="text-sm font-semibold text-stone-800">{a.course_code}</p>
              <p className="text-xs text-stone-600">
                Course : {a.course_code} | {a.title} | Last Date : {formatDmy(a.last_date)}
              </p>
              <p
                className={`text-xs font-medium ${a.days_left <= 2 ? "text-rose-700" : "text-stone-500"}`}
              >
                {dueIn(a.days_left)} · {a.max_marks} marks
              </p>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

async function Events() {
  const events = await getEvents();
  return (
    <Card
      title="Events"
      icon="calendar"
      note="List your event through the events office"
      actions={[{ href: "/m/events", label: "All Events" }]}
    >
      {events.length === 0 ? (
        <EmptyState icon="calendar">No upcoming events.</EmptyState>
      ) : (
        <ul className="space-y-3">
          {events.map((e) => {
            const { day, month } = dayAndMonth(e.starts_at);
            return (
              <li key={e.id} className="flex items-center gap-3">
                <span className="flex size-12 shrink-0 flex-col items-center justify-center rounded-xl bg-brand-700 leading-none text-white">
                  <span className="text-lg font-bold">{day}</span>
                  <span className="text-[10px] font-semibold tracking-wider uppercase">
                    {month}
                  </span>
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-stone-800">{e.title}</p>
                  <p className="flex items-center gap-1 text-xs text-stone-500">
                    <Icon name="mapPin" className="size-3.5" />
                    {e.venue} · {formatTime(e.starts_at)}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

async function PlacementDetails() {
  const drives = await getPlacementDrives();
  return (
    <Card
      title="Placement Details"
      icon="briefcase"
      note="* Drives you are eligible for"
      actions={[{ href: "/m/placement-drives", label: "Placement Portal" }]}
    >
      {drives.length === 0 ? (
        <EmptyState icon="briefcase">No Drives Available</EmptyState>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {drives.map((d) => (
            <li key={d.id} className="rounded-xl p-3 ring-1 ring-stone-200">
              <p className="flex items-center gap-2 font-semibold text-stone-800">
                <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-marigold-100 text-xs font-bold text-brand-900">
                  {initials(d.company)}
                </span>
                {d.company}
              </p>
              <p className="mt-1 text-xs text-stone-600">{d.role}</p>
              <p className="text-xs text-stone-600">Package (CTC): ₹{d.package_lpa} LPA</p>
              <p className="text-xs text-stone-500">
                Drive {formatDmy(d.drive_date)} · Register by{" "}
                <span className="font-medium text-rose-700">{formatDmy(d.register_by)}</span>
              </p>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

async function CampusDriveNotifications() {
  const drives = await getPendingDrives();
  if (drives.length === 0) return null;
  return (
    <PlacementDriveDialog
      drives={drives.map((d) => ({
        id: d.id,
        company: d.company,
        role: d.role,
        packageLabel: `₹${d.package_lpa} LPA`,
        driveDate: formatDmy(d.drive_date),
        registerBy: formatDmy(d.register_by),
      }))}
    />
  );
}
