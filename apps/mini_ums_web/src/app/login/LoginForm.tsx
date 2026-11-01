"use client";

import { useActionState, useRef, useState } from "react";
import { login, type LoginState } from "@/app/actions";
import { Icon } from "@/components/icons";
import type { DemoAccount } from "@/lib/types";

type Props = { next?: string; expired: boolean; demoAccounts: DemoAccount[] };

export function LoginForm({ next, expired, demoAccounts }: Props) {
  const [state, formAction, pending] = useActionState<LoginState, FormData>(login, {});
  const [showPassword, setShowPassword] = useState(false);
  const regNoRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  function fill(account: DemoAccount) {
    if (regNoRef.current) regNoRef.current.value = account.reg_no;
    if (passwordRef.current) passwordRef.current.value = account.password;
    passwordRef.current?.focus();
  }

  return (
    <>
      <form
        action={formAction}
        className="mt-8 w-full rounded-2xl bg-white p-8 shadow-lg shadow-brand-900/5 ring-1 ring-stone-200"
      >
        <h1 className="text-2xl font-semibold text-stone-900">Log in</h1>
        <p className="mt-1 text-sm text-stone-500">Use your registration number and password.</p>

        {expired && !state.error && (
          <p className="mt-5 flex gap-2 rounded-lg bg-marigold-50 px-3 py-2 text-sm text-marigold-500 ring-1 ring-marigold-200">
            <Icon name="clock" className="size-5 shrink-0" />
            Your session ended. Please log in again.
          </p>
        )}
        {state.error && (
          <p
            role="alert"
            className="mt-5 flex gap-2 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200"
          >
            <Icon name="alert" className="size-5 shrink-0" />
            {state.error}
          </p>
        )}

        {next && <input type="hidden" name="next" value={next} />}

        <label className="mt-6 block text-sm font-medium text-stone-700" htmlFor="reg_no">
          Registration number
        </label>
        <div className="relative mt-1.5">
          <input
            ref={regNoRef}
            id="reg_no"
            name="reg_no"
            inputMode="numeric"
            autoComplete="username"
            required
            defaultValue={state.regNo}
            placeholder="e.g. 24100001"
            className="w-full rounded-lg border-0 bg-brand-50/60 py-3 pr-11 pl-4 text-stone-900 ring-1 ring-stone-200 placeholder:text-stone-400 focus:bg-white focus:ring-2 focus:ring-brand-500 focus:outline-none"
          />
          <Icon
            name="user"
            className="pointer-events-none absolute top-1/2 right-3.5 size-5 -translate-y-1/2 text-stone-400"
          />
        </div>

        <label className="mt-4 block text-sm font-medium text-stone-700" htmlFor="password">
          Password
        </label>
        <div className="relative mt-1.5">
          <input
            ref={passwordRef}
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            required
            className="w-full rounded-lg border-0 bg-brand-50/60 py-3 pr-11 pl-4 text-stone-900 ring-1 ring-stone-200 focus:bg-white focus:ring-2 focus:ring-brand-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? "Hide password" : "Show password"}
            className="absolute top-1/2 right-2 -translate-y-1/2 rounded-md p-1.5 text-stone-500 hover:bg-stone-100 hover:text-stone-700"
          >
            <Icon name={showPassword ? "eyeOff" : "eye"} className="size-5" />
          </button>
        </div>

        <button
          type="submit"
          disabled={pending}
          className="mt-6 w-full rounded-lg bg-brand-700 py-3 font-semibold text-white shadow-sm transition hover:bg-brand-800 focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 focus-visible:outline-none disabled:opacity-60"
        >
          {pending ? "Logging in…" : "Log in"}
        </button>

        <details className="group mt-4 text-center text-sm">
          <summary className="cursor-pointer list-none text-brand-700 hover:underline">
            Forgot your password?
          </summary>
          <p className="mt-2 rounded-lg bg-stone-50 px-3 py-2 text-left text-stone-600">
            Password resets go through the IT helpdesk with your registered email. In this demo,
            use one of the demo accounts below.
          </p>
        </details>
      </form>

      {demoAccounts.length > 0 && (
        <section className="mt-6 w-full rounded-2xl border border-dashed border-brand-300 bg-white/80 p-5 backdrop-blur">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-brand-800">
            <Icon name="sparkle" className="size-4" />
            Demo accounts (development only)
          </h2>
          <p className="mt-1 text-xs text-stone-500">
            Every account uses the password{" "}
            <code className="rounded bg-stone-100 px-1 py-0.5 font-mono text-stone-700">
              {demoAccounts[0]!.password}
            </code>
            . Click one to fill the form.
          </p>
          <ul className="mt-3 space-y-1.5">
            {demoAccounts.map((account) => (
              <li key={account.reg_no}>
                <button
                  type="button"
                  onClick={() => fill(account)}
                  className="w-full rounded-lg px-3 py-2 text-left ring-1 ring-stone-200 transition hover:bg-brand-50 hover:ring-brand-300"
                >
                  <span className="flex items-baseline justify-between gap-3">
                    <span className="font-medium text-stone-800">{account.name}</span>
                    <span className="font-mono text-xs text-stone-500">{account.reg_no}</span>
                  </span>
                  <span className="mt-0.5 block text-xs text-stone-500">{account.scenario}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
