"use client";

import Link from "next/link";
import { type ReactNode, startTransition, useActionState, useRef, useState } from "react";
import { createTicket, type CreateState } from "@/app/(rms)/rms/actions";
import { Icon } from "@/components/icons";
import type { RmsCatalogue } from "@/lib/types";
import { StatusChip } from "./StatusChip";

type Props = { catalogue: RmsCatalogue; defaultBlock: string | null; defaultRoom: string | null };

/** Log Request: declarations, then the form, then a duplicate prompt or the confirmation. */
export function LogRequest(props: Props) {
  // A new round remounts the flow, clearing the form and the previous result.
  const [round, setRound] = useState(0);
  return <Flow key={round} {...props} onRestart={() => setRound((r) => r + 1)} />;
}

const EMPTY = { category: "", sub_category: "", title: "", description: "" };

/** Idempotency key for one logical request; getRandomValues also works off plain http. */
function newKey(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function Flow({ catalogue, defaultBlock, defaultRoom, onRestart }: Props & { onRestart: () => void }) {
  const { declarations, categories } = catalogue;
  const [step, setStep] = useState<"declare" | "form">("declare");
  const [fields, setFields] = useState({
    ...EMPTY,
    block: defaultBlock ?? "",
    room: defaultRoom ?? "",
  });
  const [state, dispatch, pending] = useActionState<CreateState, FormData>(createTicket, {
    kind: "idle",
  });
  const [dismissed, setDismissed] = useState<CreateState | null>(null);
  const keyRef = useRef<string | null>(null);

  const category = categories.find((c) => c.id === fields.category);

  function update(name: keyof typeof fields, value: string) {
    keyRef.current = null; // a changed request is a new request
    setFields((f) => ({ ...f, [name]: value, ...(name === "category" ? { sub_category: "" } : {}) }));
  }

  function submit(allowDuplicate: boolean) {
    keyRef.current ??= newKey();
    const data = new FormData();
    data.set("idempotency_key", keyRef.current);
    data.set("declaration_version", declarations.version);
    data.set("category", fields.category);
    data.set("sub_category", fields.sub_category);
    data.set("title", fields.title);
    data.set("description", fields.description);
    if (category?.needs_location) {
      data.set("block", fields.block);
      data.set("room", fields.room);
    }
    data.set("allow_duplicate", String(allowDuplicate));
    startTransition(() => dispatch(data));
  }

  if (state.kind === "created") {
    const t = state.ticket;
    return (
      <div className="rounded-2xl bg-white p-8 text-center shadow-sm ring-1 ring-stone-200">
        <span className="mx-auto grid size-14 place-items-center rounded-full bg-emerald-50 text-emerald-600 ring-8 ring-emerald-50/50">
          <Icon name="check" className="size-7" />
        </span>
        <h2 className="mt-4 text-xl font-semibold text-stone-900">Request logged</h2>
        <p className="mt-1 text-sm text-stone-600">
          It has gone to the {t.category_label} team. You’ll see updates in RMS History.
        </p>
        <p className="mt-6 text-xs font-semibold tracking-wider text-stone-500 uppercase">
          Request ID
        </p>
        <p className="mt-1 font-mono text-2xl font-bold tracking-wide text-brand-800">
          {t.request_id}
        </p>
        <div className="mx-auto mt-5 grid max-w-md grid-cols-2 gap-3 text-left text-sm">
          <Fact label="Ticket number" value={<span className="font-mono">{t.number}</span>} />
          <Fact label="Status" value={<StatusChip status={t.status} />} />
          <Fact label="Category" value={`${t.category_label} › ${t.sub_category}`} />
          <Fact label="Title" value={t.title} />
        </div>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link
            href={`/rms?tab=history&ticket=${t.number}`}
            className="rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800"
          >
            View in RMS History
          </Link>
          <button
            type="button"
            onClick={onRestart}
            className="rounded-lg px-4 py-2 text-sm font-medium text-stone-700 ring-1 ring-stone-300 hover:bg-stone-50"
          >
            Log another request
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5 pt-4">
      {step === "declare" ? (
        <section aria-labelledby="declarations-title" className="px-2 sm:px-6">
          <h2 id="declarations-title" className="sr-only">
            Declarations
          </h2>
          <ul className="space-y-3">
            {declarations.items.map((item) => (
              <li key={item} className="flex gap-3 text-sm text-stone-700">
                <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-marigold-400 text-white">
                  <Icon name="check" className="size-3.5" strokeWidth={3} />
                </span>
                {item}
              </li>
            ))}
          </ul>
          <div className="mt-6 flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={() => setStep("form")}
              className="rounded-lg bg-marigold-400 px-6 py-2 text-sm font-semibold text-brand-950 shadow-sm hover:bg-marigold-300"
            >
              Agree &amp; Proceed
            </button>
            <p className="text-xs text-stone-400">Declarations version {declarations.version}</p>
          </div>
        </section>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(false);
          }}
          className="space-y-6 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-stone-200"
        >
          <fieldset>
            <legend className="text-sm font-semibold text-stone-800">Category</legend>
            <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {categories.map((c) => (
                <label
                  key={c.id}
                  className="flex cursor-pointer flex-col rounded-xl px-3 py-2.5 ring-1 ring-stone-200 transition hover:ring-brand-300 has-checked:bg-brand-700 has-checked:text-white has-checked:ring-brand-700"
                >
                  <input
                    type="radio"
                    name="category"
                    value={c.id}
                    required
                    checked={fields.category === c.id}
                    onChange={() => update("category", c.id)}
                    className="sr-only"
                  />
                  <span className="text-sm font-semibold">{c.label}</span>
                  <span className="text-xs opacity-70">{c.dept}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Sub-category" htmlFor="sub_category">
              <select
                id="sub_category"
                required
                disabled={!category}
                value={fields.sub_category}
                onChange={(e) => update("sub_category", e.target.value)}
                className={INPUT}
              >
                <option value="">{category ? "Choose…" : "Choose a category first"}</option>
                {category?.sub_categories.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </Field>
            {category?.needs_location && (
              <div className="grid grid-cols-2 gap-3">
                <Field label="Block" htmlFor="block">
                  <input
                    id="block"
                    required
                    maxLength={20}
                    value={fields.block}
                    onChange={(e) => update("block", e.target.value)}
                    className={INPUT}
                  />
                </Field>
                <Field label="Room" htmlFor="room">
                  <input
                    id="room"
                    required
                    maxLength={20}
                    value={fields.room}
                    onChange={(e) => update("room", e.target.value)}
                    className={INPUT}
                  />
                </Field>
              </div>
            )}
          </div>

          <Field label="Title" htmlFor="title">
            <input
              id="title"
              required
              minLength={3}
              maxLength={120}
              value={fields.title}
              onChange={(e) => update("title", e.target.value)}
              placeholder="e.g. Fan not working"
              className={INPUT}
            />
          </Field>

          <Field
            label="Description"
            htmlFor="description"
            hint={`${fields.description.length}/500`}
          >
            <textarea
              id="description"
              required
              minLength={10}
              maxLength={500}
              rows={4}
              value={fields.description}
              onChange={(e) => update("description", e.target.value)}
              placeholder="What’s wrong, since when, and anything staff should know before visiting."
              className={INPUT}
            />
          </Field>

          {state.kind === "duplicate" && dismissed !== state && (
            <div className="rounded-xl bg-amber-50 p-4 ring-1 ring-amber-200">
              <p className="flex items-center gap-2 font-semibold text-amber-900">
                <Icon name="info" /> {state.message}
              </p>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-white p-3 ring-1 ring-amber-100">
                <div className="min-w-0">
                  <p className="font-mono text-sm font-semibold text-brand-800">
                    {state.similar.request_id}
                  </p>
                  <p className="truncate text-sm text-stone-700">{state.similar.title}</p>
                </div>
                <StatusChip status={state.similar.status} />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  href={`/rms?tab=history&ticket=${state.similar.number}#note`}
                  className="rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800"
                >
                  Add a note to that request
                </Link>
                <button
                  type="button"
                  disabled={pending}
                  onClick={() => submit(true)}
                  className="rounded-lg px-4 py-2 text-sm font-medium text-stone-700 ring-1 ring-stone-300 hover:bg-white disabled:opacity-60"
                >
                  It’s a different issue, log it anyway
                </button>
                <button
                  type="button"
                  onClick={() => setDismissed(state)}
                  className="px-2 py-2 text-sm text-stone-500 hover:underline"
                >
                  Edit my request
                </button>
              </div>
            </div>
          )}

          {state.kind === "error" && (
            <p
              role="alert"
              className="flex gap-2 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200"
            >
              <Icon name="alert" className="size-5 shrink-0" />
              {state.message}
            </p>
          )}

          <div className="flex items-center justify-between gap-3 border-t border-stone-100 pt-5">
            <button
              type="button"
              onClick={() => setStep("declare")}
              className="text-sm font-medium text-stone-600 hover:underline"
            >
              Back to declarations
            </button>
            <button
              type="submit"
              disabled={pending}
              className="rounded-lg bg-brand-700 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-800 disabled:opacity-60"
            >
              {pending ? "Submitting…" : "Submit request"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

const INPUT =
  "w-full rounded-lg border-0 bg-white px-3 py-2 text-sm text-stone-900 ring-1 ring-stone-300 placeholder:text-stone-400 focus:ring-2 focus:ring-brand-500 focus:outline-none disabled:bg-stone-50 disabled:text-stone-400";

function Field(props: { label: string; htmlFor: string; hint?: string; children: ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <label htmlFor={props.htmlFor} className="text-sm font-semibold text-stone-800">
          {props.label}
        </label>
        {props.hint && <span className="text-xs text-stone-400">{props.hint}</span>}
      </div>
      {props.children}
    </div>
  );
}

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-lg bg-stone-50 px-3 py-2">
      <p className="text-xs text-stone-500">{label}</p>
      <div className="mt-0.5 text-stone-800">{value}</div>
    </div>
  );
}
