const R = 22;
const CIRCUMFERENCE = 2 * Math.PI * R;

/** Attendance percentage as a ring: red below the threshold, amber just above, teal beyond. */
export function AttendanceRing({ percent, threshold }: { percent: number | null; threshold: number }) {
  const value = percent ?? 0;
  const tone =
    percent === null
      ? "text-stone-300"
      : value < threshold
        ? "text-rose-600"
        : value < threshold + 5
          ? "text-marigold-500"
          : "text-brand-600";
  return (
    <div className="relative size-14 shrink-0">
      <svg viewBox="0 0 56 56" className="size-14 -rotate-90" aria-hidden="true">
        <circle cx="28" cy="28" r={R} fill="none" strokeWidth="6" className="stroke-stone-100" />
        <circle
          cx="28"
          cy="28"
          r={R}
          fill="none"
          strokeWidth="6"
          strokeLinecap="round"
          stroke="currentColor"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE * (1 - Math.min(value, 100) / 100)}
          className={tone}
        />
      </svg>
      <span className="absolute inset-0 grid place-items-center text-xs font-bold text-stone-800">
        {percent === null ? "–" : `${Math.round(value)}%`}
      </span>
    </div>
  );
}
