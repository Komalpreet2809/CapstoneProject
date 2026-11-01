import { getAnnouncements } from "@/lib/data";
import { AnnouncementStrip } from "./AnnouncementStrip";

export async function Ribbon() {
  const ribbon = (await getAnnouncements()).filter((a) => a.kind === "ribbon");
  if (ribbon.length === 0) return null;
  return (
    <AnnouncementStrip
      items={ribbon.map((a) => ({
        id: a.id,
        title: a.title,
        body: a.body,
        href: a.menu_id ? `/m/${a.menu_id}` : null,
      }))}
    />
  );
}
