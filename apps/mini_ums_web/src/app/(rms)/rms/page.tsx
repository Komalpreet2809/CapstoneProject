import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Icon, type IconName } from "@/components/icons";
import { LogRequest } from "@/components/rms/LogRequest";
import { StatusChip, statusLabel } from "@/components/rms/StatusChip";
import { FeedbackForm, NoteForm } from "@/components/rms/TicketForms";
import { ApiError } from "@/lib/api";
import { getProfile, getRmsCatalogue, getTicket, getTicketHistory } from "@/lib/data";
import { daysBetween, formatDate, formatDateTime } from "@/lib/format";
import type { Ticket, TicketDetail } from "@/lib/types";

export const metadata: Metadata = { title: "RMS" };

type Tab = "log" | "history";
type Filter = "all" | "open" | "closed";

const OPEN_STATES = new Set(["OPEN", "IN_PROGRESS", "REOPENED"]);

export default function RmsPage({ searchParams }: PageProps<"/rms">) {
  return (
    <section className="rounded-2xl bg-stone-50 shadow-xl shadow-brand-950/20">
      <Suspense fallback={<Tabs tab={null} />}>
        <Rms searchParams={searchParams} />
      </Suspense>
    </section>
  );
}

async function Rms({ searchParams }: Pick<PageProps<"/rms">, "searchParams">) {
  const params = await searchParams;
  const tab: Tab = params.tab === "history" ? "history" : "log";
  const filter: Filter = params.status === "open" || params.status === "closed" ? params.status : "all";
  const selected =
    typeof params.ticket === "string" && /^[0-9]{5}$/.test(params.ticket) ? params.ticket : null;
  return (
    <>
      <Tabs tab={tab} />
      <div className="px-4 pt-2 pb-8 sm:px-8">
        {tab === "log" ? <LogTab /> : <HistoryTab filter={filter} selected={selected} />}
      </div>
    </>
  );
}

/** Two icon tabs on a raised card at the top of the panel, as in the RMS module. */
function Tabs({ tab }: { tab: Tab | null }) {
  const tabs: { id: Tab; label: string; href: string; icon: IconName }[] = [
    { id: "log", label: "Log Request", href: "/rms", icon: "chat" },
    { id: "history", label: "RMS History", href: "/rms?tab=history", icon: "list" },
  ];
  return (
    <nav aria-label="RMS" className="flex justify-center">
      <div className="-mt-5 flex overflow-hidden rounded-xl bg-white shadow-md ring-1 ring-stone-200">
        {tabs.map((t) => {
          const active = tab === t.id;
          return (
            <Link
              key={t.id}
              href={t.href}
              aria-current={active ? "page" : undefined}
              className={`flex w-32 flex-col items-center gap-1 px-4 py-3 text-sm font-semibold transition-colors ${
                active ? "text-marigold-500" : "text-stone-700 hover:bg-stone-50"
              }`}
            >
              <Icon name={t.icon} className="size-8" />
              {t.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

async function LogTab() {
  const [catalogue, profile] = await Promise.all([getRmsCatalogue(), getProfile()]);
  return (
    <LogRequest
      catalogue={catalogue}
      defaultBlock={profile.hostel_block}
      defaultRoom={profile.room}
    />
  );
}

async function HistoryTab({ filter, selected }: { filter: Filter; selected: string | null }) {
  const [history, detail] = await Promise.all([
    getTicketHistory(),
    selected ? getTicket(selected).catch(notFoundAsNull) : null,
  ]);
  const { counts, tickets } = history;
  const shown = tickets.filter((t) =>
    filter === "all" ? true : filter === "open" ? OPEN_STATES.has(t.status) : !OPEN_STATES.has(t.status),
  );
  const ratingPending = tickets.filter((t) => t.can_give_feedback).length;

  const pills: { id: Filter; label: string; count: number; tone: string }[] = [
    { id: "all", label: "Total", count: counts.total, tone: "bg-marigold-400 text-brand-950" },
    { id: "open", label: "Open", count: counts.open, tone: "bg-rose-800 text-white" },
    { id: "closed", label: "Closed", count: counts.closed, tone: "bg-emerald-800 text-white" },
  ];

  return (
    <div className="space-y-5">
      <div className="-mx-4 flex flex-wrap items-center justify-around gap-3 bg-brand-50 px-4 py-4 sm:-mx-8">
        {pills.map((p) => (
          <Link
            key={p.id}
            href={p.id === "all" ? "/rms?tab=history" : `/rms?tab=history&status=${p.id}`}
            aria-current={filter === p.id ? "true" : undefined}
            className={`flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-semibold shadow-sm transition ${p.tone} ${
              filter === p.id ? "ring-4 ring-white" : "opacity-80 hover:opacity-100"
            }`}
          >
            {p.label}
            <span className="rounded-md bg-black/25 px-1.5 text-xs text-white">{p.count}</span>
          </Link>
        ))}
      </div>
      {ratingPending > 0 && (
        <p className="text-center text-sm text-stone-600">
          Rating pending for {ratingPending} closed request{ratingPending === 1 ? "" : "s"}.
        </p>
      )}

      {shown.length === 0 ? (
        <p className="rounded-xl bg-white p-8 text-center text-sm text-stone-500 ring-1 ring-stone-200">
          {tickets.length === 0 ? (
            <>
              You haven’t logged any requests yet.{" "}
              <Link href="/rms" className="font-semibold text-brand-700">
                Log a request
              </Link>
            </>
          ) : (
            "No requests to display."
          )}
        </p>
      ) : (
        <ul className="space-y-4">
          {shown.map((t) => (
            <li key={t.number}>
              <TicketCard
                ticket={t}
                detail={t.number === detail?.number ? detail : null}
                filter={filter}
              />
            </li>
          ))}
        </ul>
      )}
      {selected && !detail && (
        <p className="text-center text-sm text-rose-700">That request wasn’t found.</p>
      )}
    </div>
  );
}

function notFoundAsNull(err: unknown): null {
  if (err instanceof ApiError && err.status === 404) return null;
  throw err;
}

function TicketCard({
  ticket: t,
  detail,
  filter,
}: {
  ticket: Ticket;
  detail: TicketDetail | null;
  filter: Filter;
}) {
  const base = filter === "all" ? "/rms?tab=history" : `/rms?tab=history&status=${filter}`;
  const days = daysBetween(t.created_at, t.closed_at);
  const statusBar = OPEN_STATES.has(t.status) ? "border-rose-600" : "border-emerald-600";

  return (
    <article
      id={`t${t.number}`}
      className={`scroll-mt-6 rounded-xl bg-white p-5 shadow-sm ring-1 ${detail ? "ring-2 ring-brand-400" : "ring-stone-200"}`}
    >
      <div className="flex items-start justify-between gap-3">
        <span className={`border-l-4 pl-2 ${statusBar}`}>
          <StatusChip status={t.status} />
        </span>
        <div className="flex items-center gap-2">
          {t.can_give_feedback && (
            <Link
              href={`${base}&ticket=${t.number}#t${t.number}`}
              scroll={false}
              className="flex items-center gap-1 rounded-full bg-marigold-400 px-3 py-1 text-xs font-semibold text-brand-950 hover:bg-marigold-300"
            >
              <Icon name="pencil" className="size-3.5" /> Feedback
            </Link>
          )}
          <Link
            href={detail ? `${base}#t${t.number}` : `${base}&ticket=${t.number}#t${t.number}`}
            scroll={false}
            aria-expanded={Boolean(detail)}
            aria-label={detail ? "Hide details" : "Show details"}
            className="grid size-7 place-items-center rounded-full bg-marigold-400 text-brand-950 hover:bg-marigold-300"
          >
            <Icon name={detail ? "x" : "info"} className="size-4" />
          </Link>
        </div>
      </div>

      <dl className="mt-3 grid gap-x-6 gap-y-0.5 text-xs text-stone-600 sm:grid-cols-2">
        <div>
          <dt className="inline font-medium">SubCategory: </dt>
          <dd className="inline">
            {t.category_label} › {t.sub_category}
          </dd>
        </div>
        <div>
          <dt className="inline font-medium">Request: </dt>
          <dd className="inline font-mono">{t.request_id}</dd>
        </div>
        <div>
          <dt className="inline font-medium">Dated: </dt>
          <dd className="inline">{formatDate(t.created_at)}</dd>
        </div>
        <div>
          <dt className="inline font-medium">{t.closed_at ? "Resolved in: " : "Open for: "}</dt>
          <dd className="inline">
            {days} day{days === 1 ? "" : "s"}
          </dd>
        </div>
        {t.block && t.room && (
          <div>
            <dt className="inline font-medium">Location: </dt>
            <dd className="inline">
              {t.block}, room {t.room}
            </dd>
          </div>
        )}
      </dl>

      <h3 className="mt-3 font-semibold text-stone-900">{t.title}</h3>
      <p className="mt-2 rounded-lg bg-brand-50 px-4 py-3 text-sm whitespace-pre-line text-stone-700">
        {t.description}
      </p>
      {t.closing_remarks && (
        <p className="mt-2 rounded-lg bg-marigold-50 px-4 py-3 text-sm text-stone-700 ring-1 ring-marigold-100">
          <strong className="text-stone-900">Closing Remarks: </strong>
          {t.closing_remarks}
        </p>
      )}
      {t.feedback && (
        <p className="mt-2 text-sm text-stone-600">
          Your feedback: {t.feedback.resolved ? "resolved" : "not resolved"} ·{" "}
          <span className="text-marigold-500">{"★".repeat(t.feedback.rating)}</span>
          <span className="text-stone-300">{"★".repeat(5 - t.feedback.rating)}</span>
          {t.feedback.comment && <> · “{t.feedback.comment}”</>}
        </p>
      )}

      {detail && <TicketDetails ticket={detail} />}
    </article>
  );
}

function TicketDetails({ ticket: t }: { ticket: TicketDetail }) {
  return (
    <div className="mt-5 space-y-5 border-t border-stone-100 pt-5">
      <section>
        <h4 className="text-sm font-semibold text-stone-800">Timeline</h4>
        <ol className="mt-3 space-y-4 border-l-2 border-stone-200 pl-5">
          {t.events.map((e, i) => (
            <li key={i} className="relative">
              <span className="absolute top-1 -left-[27px] size-3 rounded-full bg-brand-600 ring-4 ring-white" />
              <p className="text-sm font-medium text-stone-800">
                {e.status_from === e.status_to
                  ? `Note from ${e.actor === "student" ? "you" : "staff"}`
                  : statusLabel(e.status_to)}
              </p>
              {e.note && <p className="text-sm text-stone-600">{e.note}</p>}
              <p className="text-xs text-stone-400">
                {formatDateTime(e.at)} · {e.actor === "student" ? "You" : "Staff"}
              </p>
            </li>
          ))}
        </ol>
      </section>
      {t.can_give_feedback && <FeedbackForm number={t.number} />}
      {t.status !== "CLOSED" && <NoteForm number={t.number} />}
    </div>
  );
}
