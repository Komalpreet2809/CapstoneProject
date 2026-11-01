"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { logout } from "@/app/actions";
import { Icon } from "@/components/icons";
import { initials } from "@/lib/format";

type Props = {
  name: string;
  regNo: string;
  vid: string;
  programme: string;
  section: string;
  term: string;
};

export function IdentityMenu({ name, regNo, vid, programme, section, term }: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    const onClick = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative shrink-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="true"
        className="flex items-center gap-2.5 rounded-xl py-1 pr-1 pl-2 hover:bg-stone-100"
      >
        <span className="hidden max-w-60 text-right leading-tight xl:block">
          <span className="block text-sm font-semibold text-stone-800">{name}</span>
          <span className="block text-[11px] text-stone-500">
            VID: <span className="font-mono">{vid}</span> | Section: {section}
          </span>
          <span className="block truncate text-[11px] text-stone-500">{programme}</span>
        </span>
        <span className="grid size-10 place-items-center rounded-full bg-brand-700 text-sm font-semibold text-white ring-2 ring-marigold-300">
          {initials(name)}
        </span>
        <Icon name="chevronDown" className="size-4 text-stone-500" />
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-72 animate-fade-in overflow-hidden rounded-xl bg-white shadow-xl ring-1 ring-stone-200">
          <div className="bg-brand-800 px-4 py-4 text-white">
            <p className="font-semibold">{name}</p>
            <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-xs text-brand-100">
              <dt>Reg. No.</dt>
              <dd className="font-mono text-white">{regNo}</dd>
              <dt>VID</dt>
              <dd className="font-mono text-white">{vid}</dd>
              <dt>Section</dt>
              <dd className="text-white">
                {section} · Term {term}
              </dd>
            </dl>
            <p className="mt-2 text-xs text-brand-100">{programme}</p>
          </div>
          <ul className="p-1.5 text-sm">
            <li>
              <Link
                href="/m/my-profile"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-stone-700 hover:bg-stone-100"
              >
                <Icon name="user" className="size-4" /> My Profile
              </Link>
            </li>
            <li>
              <Link
                href="/m/change-password"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-stone-700 hover:bg-stone-100"
              >
                <Icon name="lock" className="size-4" /> Change Password
              </Link>
            </li>
            <li>
              <form action={logout}>
                <button
                  type="submit"
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-rose-700 hover:bg-rose-50"
                >
                  <Icon name="logout" className="size-4" /> Log out
                </button>
              </form>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
