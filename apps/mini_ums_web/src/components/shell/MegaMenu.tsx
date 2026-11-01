"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { Icon } from "@/components/icons";
import { entryHref } from "@/lib/menu";
import { toggleQuickLink, useQuickLinks } from "@/lib/quickLinks";
import type { Menu, MenuEntry } from "@/lib/types";

const ALL = "all"; // small screens: every menu stacked in one panel
const QUICK_LINKS = "quick-links";

/**
 * Five top-level menus, each opening a full-width panel of grouped links. Click opens;
 * while one is open, hovering another switches to it; Escape or a click outside closes.
 * Quick Links shows the student's own pins instead of fixed groups.
 */
export function MegaMenu({ menus }: { menus: Menu[] }) {
  const [open, setOpen] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const pins = useQuickLinks();
  const byId = useMemo(
    () => new Map(menus.flatMap((m) => m.groups.flatMap((g) => g.entries)).map((e) => [e.id, e])),
    [menus],
  );

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(null);
    const onClick = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(null);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open]);

  const shown = open === ALL ? menus : menus.filter((m) => m.id === open);
  const close = () => setOpen(null);
  const pinned = pins.flatMap((id) => byId.get(id) ?? []);

  return (
    <div ref={rootRef} className="flex h-full items-stretch">
      <button
        type="button"
        onClick={() => setOpen((o) => (o === ALL ? null : ALL))}
        aria-expanded={open === ALL}
        className="flex items-center gap-1.5 self-center rounded-lg px-2.5 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100 lg:hidden"
      >
        <Icon name="menu" />
        <span className="hidden sm:inline">Menu</span>
      </button>

      <nav aria-label="Main menu" className="hidden items-stretch lg:flex">
        {menus.map((menu) => {
          const isOpen = open === menu.id;
          return (
            <button
              key={menu.id}
              type="button"
              aria-expanded={isOpen}
              aria-controls="mega-panel"
              onClick={() => setOpen(isOpen ? null : menu.id)}
              // Only real pointer movement switches menus: when content streams in and the
              // header shifts under a resting cursor, the browser reports zero movement.
              onPointerMove={(e) => {
                if ((e.movementX || e.movementY) && open && open !== ALL && !isOpen) {
                  setOpen(menu.id);
                }
              }}
              className={`flex items-center gap-1 border-b-2 px-2.5 text-sm font-medium whitespace-nowrap transition-colors xl:px-3 ${
                isOpen
                  ? "border-marigold-400 text-brand-800"
                  : "border-transparent text-stone-700 hover:text-brand-700"
              }`}
            >
              {menu.label}
              <Icon
                name="chevronDown"
                className={`size-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
              />
            </button>
          );
        })}
      </nav>

      {shown.length > 0 && (
        <div
          id="mega-panel"
          className="absolute inset-x-0 top-full max-h-[calc(100vh-8rem)] animate-fade-in overflow-y-auto border-t border-stone-200 bg-white shadow-xl shadow-stone-900/10"
        >
          {shown.map((menu) => (
            <section key={menu.id} className="mx-auto max-w-7xl px-6 py-6 lg:px-8">
              <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-brand-800">
                <span className="h-5 w-1 rounded-full bg-marigold-400" />
                {menu.label}
              </h2>
              {menu.id === QUICK_LINKS ? (
                <QuickLinksPanel entries={pinned} onNavigate={close} />
              ) : (
                <div className="columns-[14rem] gap-x-8">
                  {menu.groups.map((group) => (
                    <div key={group.label} className="mb-6 break-inside-avoid">
                      <h3 className="border-b border-stone-200 pb-1.5 text-xs font-semibold tracking-wider text-stone-500 uppercase">
                        {group.label}
                      </h3>
                      <ul className="mt-2 space-y-0.5">
                        {group.entries.map((entry) => (
                          <li key={entry.id}>
                            <Link
                              href={entryHref(entry)}
                              onClick={close}
                              className="block rounded-md px-2 py-1 text-sm text-stone-700 transition-colors hover:bg-brand-50 hover:text-brand-800"
                            >
                              {entry.label}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

function QuickLinksPanel({ entries, onNavigate }: { entries: MenuEntry[]; onNavigate: () => void }) {
  if (entries.length === 0) {
    return (
      <p className="flex items-center gap-2 text-sm text-stone-600">
        <Icon name="star" className="size-5 text-marigold-400" />
        No quick link available. Search the menu and tap the star next to a result to add one.
      </p>
    );
  }
  return (
    <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {entries.map((entry) => (
        <li
          key={entry.id}
          className="flex items-center rounded-lg ring-1 ring-stone-200 hover:ring-brand-300"
        >
          <Link
            href={entryHref(entry)}
            onClick={onNavigate}
            className="flex-1 px-3 py-2 text-sm text-stone-700 hover:text-brand-800"
          >
            {entry.label}
          </Link>
          <button
            type="button"
            onClick={() => toggleQuickLink(entry.id)}
            aria-label={`Remove ${entry.label} from Quick Links`}
            className="mr-1 rounded-md p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700"
          >
            <Icon name="x" className="size-4" />
          </button>
        </li>
      ))}
    </ul>
  );
}
