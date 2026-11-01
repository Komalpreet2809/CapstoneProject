import type { Menu, MenuCatalogue, MenuEntry, MenuGroup } from "./types";

/** Built pages have a route; every other entry opens the shared placeholder page. */
export function entryHref(entry: MenuEntry): string {
  return entry.route ?? `/m/${entry.id}`;
}

export type Located = { menu: Menu; group: MenuGroup; entry: MenuEntry };

export function allEntries(catalogue: MenuCatalogue): Located[] {
  return catalogue.menu.flatMap((menu) =>
    menu.groups.flatMap((group) => group.entries.map((entry) => ({ menu, group, entry }))),
  );
}

export function findEntry(catalogue: MenuCatalogue, id: string): Located | undefined {
  return allEntries(catalogue).find((l) => l.entry.id === id);
}

export function entriesById(catalogue: MenuCatalogue, ids: string[]): MenuEntry[] {
  const byId = new Map(allEntries(catalogue).map((l) => [l.entry.id, l.entry]));
  return ids.flatMap((id) => byId.get(id) ?? []);
}
