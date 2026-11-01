"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Icon, type IconName } from "@/components/icons";

type Item = { href: string; label: string; icon: IconName };

/** Left rail: icon with its label underneath; « collapses it to icons only. */
export function SidebarLinks({ items }: { items: Item[] }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  return (
    <aside
      className={`relative hidden shrink-0 bg-brand-800 transition-[width] md:block ${collapsed ? "w-14" : "w-24"}`}
    >
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        aria-label={collapsed ? "Expand side menu" : "Collapse side menu"}
        aria-expanded={!collapsed}
        className="absolute top-3 -right-3 z-10 grid size-6 place-items-center rounded-md bg-white text-stone-600 shadow ring-1 ring-stone-200 hover:text-brand-700"
      >
        <Icon name="chevronsLeft" className={`size-3.5 ${collapsed ? "rotate-180" : ""}`} />
      </button>
      <nav aria-label="Side menu" className="sticky top-16 flex flex-col pt-2">
        {items.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              title={collapsed ? item.label : undefined}
              className={`flex flex-col items-center gap-1 border-b border-white/10 border-l-4 px-1 py-3.5 text-center transition-colors ${
                active
                  ? "border-l-marigold-300 bg-brand-950/40 text-white"
                  : "border-l-transparent text-brand-100 hover:bg-brand-950/25 hover:text-white"
              }`}
            >
              <Icon name={item.icon} className="size-6" />
              <span className={`text-[11px] leading-tight font-semibold ${collapsed ? "sr-only" : ""}`}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
