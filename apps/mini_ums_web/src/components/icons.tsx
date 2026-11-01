import type { SVGProps } from "react";

// Small stroke icon set, drawn for this project (24×24 grid, currentColor).
const paths = {
  home: "M3 10.5 12 3l9 7.5M5 9.5V20h5v-6h4v6h5V9.5",
  book: "M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15ZM4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5",
  mail: "M3 6h18v12H3zM3 7l9 6 9-6",
  calendar: "M4 6h16v15H4zM4 10h16M8 3v4M16 3v4",
  lifebuoy:
    "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 5a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM5.6 5.6l3.6 3.6M14.8 14.8l3.6 3.6M18.4 5.6l-3.6 3.6M9.2 14.8l-3.6 3.6",
  search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14Zm9 16-4-4",
  user: "M12 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM4 21a8 8 0 0 1 16 0",
  logout: "M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10",
  chevronDown: "m6 9 6 6 6-6",
  chevronRight: "m9 6 6 6-6 6",
  chevronLeft: "m15 6-6 6 6 6",
  eye: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Zm10-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z",
  eyeOff:
    "M3 3l18 18M10.6 5.1A10 10 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.2 4.2M6.1 6.1A17 17 0 0 0 2 12s3.5 7 10 7a9.6 9.6 0 0 0 5-1.4M9.9 9.9a3 3 0 0 0 4.2 4.2",
  wallet: "M3 7h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H3zM3 7l13-4v4M16 13.5h2",
  clipboard: "M9 4h6v3H9zM7 5H5v16h14V5h-2M8.5 12l2 2 4-4",
  ticket: "M3 8a2 2 0 0 0 0 4v0a2 2 0 0 1 0 4v3h18v-3a2 2 0 0 1 0-4 2 2 0 0 0 0-4V5H3zM14 5v14",
  briefcase: "M3 8h18v12H3zM8 8V5h8v3M3 13h18",
  megaphone: "M3 10v4h3l7 5V5L6 10H3ZM17 8a5 5 0 0 1 0 8",
  bell: "M6 16V11a6 6 0 0 1 12 0v5l2 2H4l2-2ZM10 20a2 2 0 0 0 4 0",
  clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 4v5l3 2",
  mapPin: "M12 21s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12Zm0-14a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5Z",
  alert: "M12 3 2 20h20L12 3Zm0 6v5m0 3v.5",
  info: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 8v5m0-8.5V8",
  check: "m5 12 5 5 9-10",
  x: "M6 6l12 12M18 6 6 18",
  arrowRight: "M4 12h15m-6-6 6 6-6 6",
  plus: "M12 5v14M5 12h14",
  star: "m12 3 2.8 5.8 6.2.9-4.5 4.4 1 6.3L12 17.5l-5.5 2.9 1-6.3L3 9.7l6.2-.9L12 3Z",
  grid: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z",
  lock: "M6 11h12v10H6zM8.5 11V7.5a3.5 3.5 0 0 1 7 0V11",
  sparkle: "M12 3v4m0 10v4M3 12h4m10 0h4M6 6l2.5 2.5m7 7L18 18m0-12-2.5 2.5m-7 7L6 18",
  menu: "M4 6h16M4 12h16M4 18h16",
  chat: "M4 5h16v11H10l-4 4v-4H4zM8 9.5h8M8 12.5h5",
  list: "M10 6h10M10 12h10M10 18h10M4 5h3v3H4zM4 11h3v3H4zM4 17h3v3H4z",
  pencil: "M4 20h4L19 9l-4-4L4 16v4ZM13.5 6.5l4 4",
  phone: "M7 3h10v18H7zM11 18h2",
  video: "M3 7h12v10H3zM15 10.5 21 7v10l-6-3.5",
  heart: "M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z",
  chevronsLeft: "m11 6-6 6 6 6M18 6l-6 6 6 6",
};

export type IconName = keyof typeof paths;

export function Icon({
  name,
  className = "size-5",
  ...props
}: { name: IconName } & SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
      {...props}
    >
      <path d={paths[name]} />
    </svg>
  );
}
