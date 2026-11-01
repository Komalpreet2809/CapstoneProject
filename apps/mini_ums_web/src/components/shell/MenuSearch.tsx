"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type KeyboardEvent, useEffect, useId, useMemo, useRef, useState } from "react";
import { Icon } from "@/components/icons";
import { toggleQuickLink, useQuickLinks } from "@/lib/quickLinks";

export type SearchItem = {
  id: string;
  label: string;
  href: string;
  path: string;
  keywords: string[];
};

const MAX_RESULTS = 8;

function rank(item: SearchItem, q: string): number {
  const label = item.label.toLowerCase();
  if (label.startsWith(q)) return 0;
  if (label.split(/\W+/).some((word) => word.startsWith(q))) return 1;
  if (item.keywords.some((k) => k.toLowerCase().startsWith(q))) return 2;
  if (label.includes(q)) return 3;
  if (item.path.toLowerCase().includes(q)) return 4;
  return -1;
}

/** Search over every menu entry (labels, groups and keywords). Press "/" to focus. */
export function MenuSearch({ items }: { items: SearchItem[] }) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const pins = useQuickLinks();
  const router = useRouter();
  const listId = useId();

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return items
      .map((item) => ({ item, score: rank(item, q) }))
      .filter((r) => r.score >= 0)
      .sort((a, b) => a.score - b.score || a.item.label.localeCompare(b.item.label))
      .slice(0, MAX_RESULTS)
      .map((r) => r.item);
  }, [items, query]);

  useEffect(() => {
    const onKey = (e: globalThis.KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (e.key !== "/" || target.closest("input, textarea, select, [contenteditable]")) return;
      e.preventDefault();
      inputRef.current?.focus();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  function go(item: SearchItem) {
    setQuery("");
    inputRef.current?.blur();
    router.push(item.href);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown" && results.length) {
      e.preventDefault();
      setActive((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp" && results.length) {
      e.preventDefault();
      setActive((i) => (i - 1 + results.length) % results.length);
    } else if (e.key === "Enter" && results[active]) {
      e.preventDefault();
      go(results[active]);
    } else if (e.key === "Escape") {
      setQuery("");
      inputRef.current?.blur();
    }
  }

  const expanded = focused && query.trim().length > 0;

  return (
    <div className="relative w-40 min-w-0 shrink transition-[width] focus-within:w-72 xl:w-52">
      <Icon
        name="search"
        className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-stone-400"
      />
      <input
        ref={inputRef}
        type="search"
        role="combobox"
        aria-label="Search the menu"
        aria-expanded={expanded}
        aria-controls={listId}
        aria-activedescendant={expanded && results[active] ? `${listId}-${active}` : undefined}
        aria-autocomplete="list"
        placeholder="Search menu…"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setActive(0);
        }}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onKeyDown={onKeyDown}
        className="w-full rounded-full border-0 bg-stone-100 py-2 pr-10 pl-9 text-sm text-stone-800 ring-1 ring-transparent placeholder:text-stone-500 focus:bg-white focus:ring-brand-400 focus:outline-none [&::-webkit-search-cancel-button]:hidden"
      />
      <kbd className="pointer-events-none absolute top-1/2 right-3 hidden -translate-y-1/2 rounded border border-stone-300 bg-white px-1.5 font-mono text-[10px] text-stone-500 sm:block">
        /
      </kbd>

      {expanded && (
        <ul
          id={listId}
          role="listbox"
          className="absolute right-0 left-0 z-50 mt-2 max-h-96 overflow-y-auto rounded-xl bg-white p-1.5 shadow-xl ring-1 ring-stone-200 sm:left-auto sm:w-96"
        >
          {results.length === 0 && (
            <li className="px-3 py-2 text-sm text-stone-500">No menu entries match “{query}”.</li>
          )}
          {results.map((item, i) => {
            const isPinned = pins.includes(item.id);
            return (
              <li
                key={item.id}
                id={`${listId}-${i}`}
                role="option"
                aria-selected={i === active}
                onMouseEnter={() => setActive(i)}
                className={`flex items-center rounded-lg ${i === active ? "bg-brand-50" : ""}`}
              >
                <Link
                  href={item.href}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => setQuery("")}
                  className="min-w-0 flex-1 px-3 py-2"
                >
                  <span className="block text-sm font-medium text-stone-800">{item.label}</span>
                  <span className="block text-xs text-stone-500">{item.path}</span>
                </Link>
                <button
                  type="button"
                  tabIndex={-1}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => toggleQuickLink(item.id)}
                  aria-pressed={isPinned}
                  aria-label={isPinned ? "Remove from Quick Links" : "Add to Quick Links"}
                  title={isPinned ? "Remove from Quick Links" : "Add to Quick Links"}
                  className="mr-1.5 rounded-md p-1.5 hover:bg-white"
                >
                  <Icon
                    name="star"
                    className={`size-4 ${isPinned ? "fill-marigold-300 text-marigold-500" : "text-stone-400"}`}
                  />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
