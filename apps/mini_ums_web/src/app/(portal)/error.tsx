"use client";

import { useEffect } from "react";
import { Icon } from "@/components/icons";

export default function PortalError({ error, retry }: { error: unknown; retry: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto mt-16 max-w-md rounded-2xl bg-white p-8 text-center shadow-sm ring-1 ring-stone-200">
      <span className="mx-auto grid size-12 place-items-center rounded-full bg-rose-50 text-rose-600">
        <Icon name="alert" className="size-6" />
      </span>
      <h1 className="mt-4 text-lg font-semibold">This page couldn’t load</h1>
      <p className="mt-1 text-sm text-stone-600">
        The portal’s services may be restarting. Your data is safe.
      </p>
      <button
        type="button"
        onClick={() => retry()}
        className="mt-6 rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800"
      >
        Try again
      </button>
    </div>
  );
}
