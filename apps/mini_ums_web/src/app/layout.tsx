import type { Metadata } from "next";
import { Suspense } from "react";
import { VoiceWidgetScript } from "@/components/VoiceWidgetScript";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mini UMS",
  description: "Demo student portal with fully synthetic data",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-stone-50 text-stone-900 antialiased">
        <div
          role="note"
          className="bg-amber-300 px-4 py-1 text-center text-xs font-semibold tracking-wide text-amber-950"
        >
          Demo – synthetic data. Not a real university system.
        </div>
        <header className="border-b border-stone-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-3">
            <span className="grid size-8 place-items-center rounded-md bg-teal-700 text-sm font-bold text-white">
              M
            </span>
            <span className="text-lg font-semibold">Mini UMS</span>
          </div>
        </header>
        {children}
        <Suspense fallback={null}>
          <VoiceWidgetScript />
        </Suspense>
      </body>
    </html>
  );
}
