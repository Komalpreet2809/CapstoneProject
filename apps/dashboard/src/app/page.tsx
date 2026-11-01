import { Suspense } from "react";
import { ServiceStatus } from "@/components/ServiceStatus";

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-semibold">System status</h1>
      <p className="mb-6 text-sm text-slate-600">
        Live readiness of every VoiceServe service. Conversations, tickets, escalations and
        analytics arrive in M6.
      </p>
      <Suspense fallback={<p className="text-sm text-slate-500">Checking services…</p>}>
        <ServiceStatus />
      </Suspense>
    </main>
  );
}
