import type { IconName } from "@/components/icons";
import { getMenu } from "@/lib/data";
import { entriesById, entryHref } from "@/lib/menu";
import { SidebarLinks } from "./SidebarLinks";

const ICONS: Record<string, IconName> = {
  dashboard: "home",
  "mobile-app": "phone",
  "live-classes": "video",
  "my-class": "clock",
  "counselling-appointment": "heart",
};

// Rail labels are short; the catalogue labels are written for menus.
const LABELS: Record<string, string> = {
  "mobile-app": "Mobile App",
  "counselling-appointment": "Counselling",
};

export async function Sidebar() {
  const catalogue = await getMenu();
  const items = entriesById(catalogue, catalogue.sidebar).map((entry) => ({
    href: entryHref(entry),
    label: LABELS[entry.id] ?? entry.label,
    icon: ICONS[entry.id] ?? ("grid" as IconName),
  }));
  return <SidebarLinks items={items} />;
}
