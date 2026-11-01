/** Univra mark: a "U" arch over a marigold keystone. Original artwork for this project. */
export function LogoMark({ className = "size-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <rect width="40" height="40" rx="10" className="fill-brand-700" />
      <path
        d="M11 10v11a9 9 0 0 0 18 0V10"
        fill="none"
        strokeWidth="5"
        strokeLinecap="round"
        className="stroke-white"
      />
      <path d="M20 23.5 23.5 30h-7Z" className="fill-marigold-300" />
    </svg>
  );
}

export function Logo({ inverted = false }: { inverted?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <LogoMark />
      <span className="leading-none">
        <span
          className={`block text-xl font-bold tracking-tight ${inverted ? "text-white" : "text-brand-800"}`}
        >
          Univra
        </span>
        <span
          className={`block text-[10px] font-medium tracking-[0.18em] uppercase ${inverted ? "text-brand-100" : "text-stone-500"}`}
        >
          Student Portal
        </span>
      </span>
    </span>
  );
}
