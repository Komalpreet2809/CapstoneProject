import type { TicketStatus } from "@/lib/types";

const STYLES: Record<TicketStatus, { label: string; className: string }> = {
  OPEN: { label: "Open", className: "bg-sky-50 text-sky-800 ring-sky-200" },
  IN_PROGRESS: { label: "In progress", className: "bg-amber-50 text-amber-800 ring-amber-200" },
  CLOSED: { label: "Closed", className: "bg-emerald-50 text-emerald-800 ring-emerald-200" },
  REOPENED: { label: "Reopened", className: "bg-rose-50 text-rose-800 ring-rose-200" },
};

export function statusLabel(status: string): string {
  return STYLES[status as TicketStatus]?.label ?? status;
}

export function StatusChip({ status }: { status: TicketStatus }) {
  const { label, className } = STYLES[status];
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${className}`}
    >
      {label}
    </span>
  );
}
