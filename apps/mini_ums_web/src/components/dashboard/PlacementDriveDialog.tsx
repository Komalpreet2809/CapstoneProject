"use client";

import Link from "next/link";
import { useEffect, useRef, useState, useTransition } from "react";
import { acknowledgeDrives } from "@/app/actions";
import { Icon } from "@/components/icons";

export type DriveRow = {
  id: number;
  company: string;
  role: string;
  packageLabel: string;
  driveDate: string;
  registerBy: string;
};

/** Pop-up after login listing new eligible drives, until read or snoozed. */
export function PlacementDriveDialog({ drives }: { drives: DriveRow[] }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  function acknowledge(action: "read" | "later") {
    setError(null);
    startTransition(async () => {
      try {
        await acknowledgeDrives(
          drives.map((d) => d.id),
          action,
        );
        ref.current?.close();
      } catch {
        setError("Couldn’t save that just now. Please try again.");
      }
    });
  }

  return (
    <dialog
      ref={ref}
      aria-labelledby="drives-title"
      className="m-auto w-[min(36rem,calc(100vw-2rem))] overflow-hidden rounded-2xl p-0 shadow-2xl"
    >
      <div className="flex items-center justify-between gap-4 border-b border-stone-200 px-6 py-4">
        <h2 id="drives-title" className="text-lg font-semibold text-stone-900">
          Campus Drive Notifications
        </h2>
        <button
          type="button"
          onClick={() => ref.current?.close()}
          aria-label="Close"
          className="rounded-full p-1.5 text-stone-500 hover:bg-stone-100"
        >
          <Icon name="x" />
        </button>
      </div>

      <div className="px-6 py-4">
        <p className="text-base font-medium text-stone-800">You are eligible for below drives</p>
        <ol className="mt-3 max-h-72 space-y-2 overflow-y-auto text-sm text-stone-700">
          {drives.map((d, i) => (
            <li key={d.id} className="flex gap-2">
              <span className="font-mono text-stone-500">{String(i + 1).padStart(2, "0")}.</span>
              <span>
                <strong className="font-semibold text-stone-900">{d.company}</strong>, {d.role} (
                {d.packageLabel}). Drive on {d.driveDate}. Registration open till{" "}
                <span className="font-medium text-rose-700">{d.registerBy}</span>.
              </span>
            </li>
          ))}
        </ol>
        <p className="mt-3 text-sm font-semibold text-stone-800">
          Check venue through the{" "}
          <Link href="/m/placement-drives" className="text-brand-700 underline">
            Placement Portal
          </Link>
          .
        </p>
        {error && <p className="mt-2 text-sm text-rose-700">{error}</p>}
      </div>

      <div className="flex justify-center gap-3 px-6 pb-5">
        <button
          type="button"
          disabled={pending}
          onClick={() => acknowledge("read")}
          className="rounded-full bg-marigold-400 px-6 py-2 text-sm font-semibold text-brand-950 hover:bg-marigold-300 disabled:opacity-60"
        >
          Mark as Read
        </button>
        <button
          type="button"
          disabled={pending}
          onClick={() => acknowledge("later")}
          className="rounded-full bg-brand-700 px-6 py-2 text-sm font-semibold text-white hover:bg-brand-800 disabled:opacity-60"
        >
          Remind me later
        </button>
      </div>
    </dialog>
  );
}
