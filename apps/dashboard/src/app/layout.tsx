import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VoiceServe Staff",
  description: "Staff dashboard for VoiceServe: conversations, tickets, escalations, analytics",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
            <span className="text-lg font-semibold">VoiceServe Staff</span>
            <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">
              Demo – synthetic data
            </span>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
