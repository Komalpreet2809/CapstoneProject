import { getMenu } from "@/lib/data";
import { allEntries, entryHref } from "@/lib/menu";
import { MegaMenu } from "./MegaMenu";
import { MenuSearch, type SearchItem } from "./MenuSearch";

/** Menus sit on the right of the header, followed by search, as in the real portal. */
export async function TopNav() {
  const catalogue = await getMenu();
  const items: SearchItem[] = allEntries(catalogue).map(({ menu, group, entry }) => ({
    id: entry.id,
    label: entry.label,
    href: entryHref(entry),
    path: menu.id === "quick-links" ? "Portal" : `${menu.label} › ${group.label}`,
    keywords: entry.keywords,
  }));
  return (
    <div className="flex h-full min-w-0 flex-1 items-center justify-end gap-2">
      <MegaMenu menus={catalogue.menu} />
      <MenuSearch items={items} />
    </div>
  );
}
