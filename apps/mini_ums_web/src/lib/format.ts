// Display formats. Everything shows campus time (IST), whatever the server's timezone.
const TZ = "Asia/Kolkata";

const date = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: TZ,
});
const shortDate = new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", timeZone: TZ });
const dateTime = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: TZ,
});
const time = new Intl.DateTimeFormat("en-IN", { hour: "2-digit", minute: "2-digit", timeZone: TZ });
const inr = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export const formatDate = (iso: string) => date.format(new Date(iso));
export const formatShortDate = (iso: string) => shortDate.format(new Date(iso));
export const formatDateTime = (iso: string) => dateTime.format(new Date(iso));
export const formatTime = (iso: string) => time.format(new Date(iso));
export const formatInr = (amount: number) => inr.format(amount);

const numericDate = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: TZ,
});

/** DD-MM-YYYY, the portal's numeric date style. */
export function formatDmy(value: string | number): string {
  const parts = numericDate.formatToParts(new Date(value));
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `${get("day")}-${get("month")}-${get("year")}`;
}

export function dayAndMonth(iso: string): { day: string; month: string } {
  const parts = shortDate.formatToParts(new Date(iso));
  return {
    day: parts.find((p) => p.type === "day")?.value ?? "",
    month: parts.find((p) => p.type === "month")?.value ?? "",
  };
}

const DAY_MS = 24 * 60 * 60 * 1000;

/** The date `days` from now, as DD-MM-YYYY (server render time). */
export function dmyInDays(days: number): string {
  return formatDmy(Date.now() + days * DAY_MS);
}

/** Whole days from `fromIso` to `toIso`, or to now when it isn't given. */
export function daysBetween(fromIso: string, toIso?: string | null): number {
  const end = toIso ? Date.parse(toIso) : Date.now();
  return Math.max(0, Math.floor((end - Date.parse(fromIso)) / DAY_MS));
}

export function dueIn(days: number): string {
  if (days < 0) return `${-days} day${days === -1 ? "" : "s"} overdue`;
  if (days === 0) return "Due today";
  if (days === 1) return "Due tomorrow";
  return `Due in ${days} days`;
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join("");
}
