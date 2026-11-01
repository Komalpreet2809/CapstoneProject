"use client";

import { useActionState, useState } from "react";
import { addNote, giveFeedback, type FormState } from "@/app/(rms)/rms/actions";
import { Icon } from "@/components/icons";

export function NoteForm({ number }: { number: string }) {
  const [state, action, pending] = useActionState<FormState, FormData>(addNote, {});
  return (
    <form id="note" action={action} className="scroll-mt-24 space-y-2">
      <input type="hidden" name="number" value={number} />
      <label htmlFor="note-text" className="text-sm font-semibold text-stone-800">
        Add a note
      </label>
      <textarea
        id="note-text"
        name="note"
        required
        minLength={3}
        maxLength={500}
        rows={3}
        placeholder="Anything new since you logged it, e.g. a better time for staff to visit."
        className="w-full rounded-lg border-0 px-3 py-2 text-sm ring-1 ring-stone-300 focus:ring-2 focus:ring-brand-500 focus:outline-none"
      />
      {state.error && <p className="text-sm text-rose-700">{state.error}</p>}
      {state.ok && !pending && <p className="text-sm text-emerald-700">Note added.</p>}
      <button
        type="submit"
        disabled={pending}
        className="rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800 disabled:opacity-60"
      >
        {pending ? "Adding…" : "Add note"}
      </button>
    </form>
  );
}

export function FeedbackForm({ number }: { number: string }) {
  const [state, action, pending] = useActionState<FormState, FormData>(giveFeedback, {});
  const [resolved, setResolved] = useState<"yes" | "no" | null>(null);
  const [rating, setRating] = useState(0);

  return (
    <form
      action={action}
      className="space-y-4 rounded-xl bg-marigold-50 p-4 ring-1 ring-marigold-200"
    >
      <input type="hidden" name="number" value={number} />
      <p className="font-semibold text-stone-900">How did we do?</p>

      <fieldset>
        <legend className="text-sm font-medium text-stone-700">Was your issue resolved?</legend>
        <div className="mt-2 flex gap-2">
          {(["yes", "no"] as const).map((value) => (
            <label
              key={value}
              className="cursor-pointer rounded-lg bg-white px-4 py-1.5 text-sm font-medium ring-1 ring-stone-300 has-checked:bg-brand-700 has-checked:text-white has-checked:ring-brand-700"
            >
              <input
                type="radio"
                name="resolved"
                value={value}
                required
                onChange={() => setResolved(value)}
                className="sr-only"
              />
              {value === "yes" ? "Yes, resolved" : "No, not resolved"}
            </label>
          ))}
        </div>
        {resolved === "no" && (
          <p className="mt-2 text-xs text-stone-600">Your request will be reopened.</p>
        )}
      </fieldset>

      <fieldset>
        <legend className="text-sm font-medium text-stone-700">Rating</legend>
        <div className="mt-1 flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <label key={n} className="cursor-pointer" title={`${n} of 5`}>
              <input
                type="radio"
                name="rating"
                value={n}
                required
                onChange={() => setRating(n)}
                className="peer sr-only"
              />
              <Icon
                name="star"
                className={`size-7 rounded peer-focus-visible:ring-2 peer-focus-visible:ring-brand-500 ${
                  n <= rating ? "fill-marigold-300 text-marigold-500" : "text-stone-300"
                }`}
              />
              <span className="sr-only">{n} of 5</span>
            </label>
          ))}
        </div>
      </fieldset>

      <textarea
        name="comment"
        maxLength={500}
        rows={2}
        placeholder="Comment (optional)"
        className="w-full rounded-lg border-0 px-3 py-2 text-sm ring-1 ring-stone-300 focus:ring-2 focus:ring-brand-500 focus:outline-none"
      />
      {state.error && <p className="text-sm text-rose-700">{state.error}</p>}
      <button
        type="submit"
        disabled={pending}
        className="rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800 disabled:opacity-60"
      >
        {pending ? "Sending…" : "Submit feedback"}
      </button>
    </form>
  );
}
