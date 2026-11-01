import type { Metadata } from "next";
import { Suspense } from "react";
import { VoiceWidgetScript } from "@/components/VoiceWidgetScript";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Univra Student Portal", template: "%s · Univra" },
  description: "Demo student portal with fully synthetic data",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-stone-100 text-stone-900 antialiased">
        <div
          role="note"
          className="bg-amber-300 px-4 py-1 text-center text-xs font-semibold tracking-wide text-amber-950"
        >
          Demo – synthetic data. Not a real university system.
        </div>
        {children}
        <Suspense fallback={null}>
          <VoiceWidgetScript />
        </Suspense>
      </body>
    </html>
  );
}
