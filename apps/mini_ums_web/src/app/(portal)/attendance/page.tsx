import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { AttendanceRing } from "@/components/dashboard/AttendanceRing";
import { Icon } from "@/components/icons";
import { getCourses } from "@/lib/data";
import { formatDateTime } from "@/lib/format";
import type { Course } from "@/lib/types";

export const metadata: Metadata = { title: "View Attendance" };

export default function AttendancePage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1 text-sm text-stone-500">
        <Link href="/" className="hover:text-brand-700">
          Dashboard
        </Link>
        <Icon name="chevronRight" className="size-4" />
        <span>Academics</span>
        <Icon name="chevronRight" className="size-4" />
        <span>Learning Management System (LMS)</span>
      </nav>
      <h1 className="text-2xl font-semibold text-stone-900">View Attendance</h1>
      <Suspense fallback={<div className="h-96 animate-pulse rounded-2xl bg-stone-200" />}>
        <Attendance />
      </Suspense>
    </div>
  );
}

function statusOf(c: Course): { label: string; className: string } {
  const a = c.attendance;
  if (a.percent === null) return { label: "No classes yet", className: "bg-stone-100 text-stone-600" };
  if (!a.meets_threshold) return { label: "Below minimum", className: "bg-rose-50 text-rose-700 ring-1 ring-rose-200" };
  if (a.percent < a.threshold + 5) return { label: "Close to minimum", className: "bg-amber-50 text-amber-800 ring-1 ring-amber-200" };
  return { label: "On track", className: "bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200" };
}

function guidance(c: Course): string {
  const a = c.attendance;
  if (a.percent === null) return "Nothing to do yet.";
  if (!a.meets_threshold) {
    return `Attend the next ${a.classes_needed} class${a.classes_needed === 1 ? "" : "es"} in a row to reach ${a.threshold}%.`;
  }
  if (a.can_miss === 0) return "Don’t miss the next class.";
  return `You can miss up to ${a.can_miss} class${a.can_miss === 1 ? "" : "es"} and stay at ${a.threshold}% or above.`;
}

async function Attendance() {
  const courses = await getCourses();
  if (courses.length === 0) {
    return (
      <p className="rounded-2xl bg-white p-8 text-center text-stone-600 shadow-sm ring-1 ring-stone-200">
        No registered courses this term.
      </p>
    );
  }
  const held = courses.reduce((sum, c) => sum + c.attendance.held, 0);
  const attended = courses.reduce((sum, c) => sum + c.attendance.attended, 0);
  const overall = held > 0 ? Math.round((attended / held) * 100) : null;
  const below = courses.filter((c) => c.attendance.meets_threshold === false);
  const threshold = courses[0]!.attendance.threshold;
  const updated = courses
    .map((c) => c.attendance.last_updated)
    .sort()
    .at(-1)!;

  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-3">
        <Tile label="Overall attendance" value={overall === null ? "–" : `${overall}%`} />
        <Tile label="Minimum required" value={`${threshold}%`} />
        <Tile
          label="Courses below minimum"
          value={String(below.length)}
          tone={below.length ? "text-rose-700" : "text-emerald-700"}
        />
      </div>

      <div className="overflow-x-auto rounded-2xl bg-white shadow-sm ring-1 ring-stone-200">
        <table className="w-full min-w-[46rem] text-left text-sm">
          <caption className="sr-only">Course-wise attendance</caption>
          <thead className="border-b border-stone-200 bg-brand-50 text-xs tracking-wide text-brand-900 uppercase">
            <tr>
              <th scope="col" className="px-4 py-3">Course</th>
              <th scope="col" className="px-4 py-3">Attended / Held</th>
              <th scope="col" className="px-4 py-3">Attendance</th>
              <th scope="col" className="px-4 py-3">Status</th>
              <th scope="col" className="px-4 py-3">What it means</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-100">
            {courses.map((c) => {
              const status = statusOf(c);
              return (
                <tr key={c.code} id={c.code} className="scroll-mt-24 target:bg-marigold-50">
                  <td className="px-4 py-3">
                    <p className="font-semibold text-stone-800">{c.code}</p>
                    <p className="text-stone-600">{c.title}</p>
                    <p className="text-xs text-stone-400">
                      {c.kind} · {c.faculty}
                    </p>
                  </td>
                  <td className="px-4 py-3 font-mono text-stone-700">
                    {c.attendance.attended} / {c.attendance.held}
                  </td>
                  <td className="px-4 py-3">
                    <AttendanceRing percent={c.attendance.percent} threshold={c.attendance.threshold} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${status.className}`}>
                      {status.label}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-stone-600">{guidance(c)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-stone-500">
        Last updated {formatDateTime(updated)}. Duty leave and make-up classes are counted once
        approved.
      </p>
    </div>
  );
}

function Tile({ label, value, tone = "text-stone-900" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-2xl bg-white px-5 py-4 shadow-sm ring-1 ring-stone-200">
      <p className="text-sm text-stone-500">{label}</p>
      <p className={`text-3xl font-bold ${tone}`}>{value}</p>
    </div>
  );
}
