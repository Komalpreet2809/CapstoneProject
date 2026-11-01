import Link from "next/link";
import type { ReactNode } from "react";
import { Icon, type IconName } from "@/components/icons";

type Action = { href: string; label: string };

type Props = {
  title: string;
  icon: IconName;
  /** Small note on the left of the footer, e.g. "* Messages sent by teachers". */
  note?: ReactNode;
  actions?: Action[];
  className?: string;
  children: ReactNode;
};

/** Dashboard card: the title is a tab on the top edge; the footer has a note and buttons. */
export function Card({ title, icon, note, actions = [], className = "", children }: Props) {
  return (
    <section
      className={`relative mt-4 flex flex-col rounded-2xl border-2 border-brand-200 bg-white shadow-sm ${className}`}
    >
      <h2 className="absolute -top-4 left-4 flex items-center gap-1.5 rounded-full bg-brand-700 px-4 py-1 text-sm font-semibold text-white shadow-sm">
        <Icon name={icon} className="size-4 text-marigold-200" />
        {title}
      </h2>
      <div className="flex-1 px-5 pt-7 pb-4">{children}</div>
      {(note || actions.length > 0) && (
        <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-stone-100 px-5 py-3">
          <p className="text-xs text-stone-500">{note}</p>
          <div className="flex gap-2">
            {actions.map((a) => (
              <Link
                key={a.href}
                href={a.href}
                className="rounded-full bg-brand-700 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-brand-800"
              >
                {a.label}
              </Link>
            ))}
          </div>
        </footer>
      )}
    </section>
  );
}

export function CardSkeleton({ className = "", rows = 4 }: { className?: string; rows?: number }) {
  return (
    <div
      aria-hidden="true"
      className={`mt-4 animate-pulse rounded-2xl border-2 border-stone-200 bg-white p-5 ${className}`}
    >
      <div className="h-6 w-32 rounded-full bg-stone-200" />
      <div className="mt-5 space-y-3">
        {Array.from({ length: rows }, (_, i) => (
          <div key={i} className="h-10 rounded-lg bg-stone-100" />
        ))}
      </div>
    </div>
  );
}

export function EmptyState({ icon, children }: { icon: IconName; children: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 py-6 text-center text-sm text-stone-500">
      <Icon name={icon} className="size-8 text-stone-300" />
      {children}
    </div>
  );
}
