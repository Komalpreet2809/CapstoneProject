/**
 * VoiceServe widget: the floating mic button and panel embedded on every Mini UMS page.
 *
 * Shipped as one framework-free script; markup and styles live in a shadow root. The host
 * page provides two same-origin endpoints (defaults below): one starts a voice session (the
 * portal token never reaches this script), one takes typed questions. Voice runs over LiveKit
 * when the host offers it; typing always works.
 *
 * States: idle -> listening (live captions) -> thinking -> speaking -> done. The confirm
 * state (Confirm / Change card) arrives with the first write actions in M4.
 */
import { type Card, renderCard } from "./cards";
import { STYLES } from "./styles";
import { type AgentState, VoiceClient } from "./voice";

export type WidgetState =
  | "idle"
  | "connecting"
  | "listening"
  | "thinking"
  | "speaking"
  | "confirm"
  | "done";

export interface VoiceServeApi {
  version: string;
  open(): void;
  close(): void;
}

interface VoiceServeConfig {
  sessionEndpoint?: string;
  textEndpoint?: string;
}

declare global {
  interface Window {
    VoiceServe?: VoiceServeApi;
    VoiceServeConfig?: VoiceServeConfig;
  }
}

type Session = {
  session_id: string;
  first_name: string;
  voice: { url: string; token: string; mode: "live" | "replay" } | null;
  voice_unavailable_reason?: string;
};

const VERSION = "0.3.0";
const HOST_ID = "voiceserve-widget";

const MIC_ICON = `<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" fill="none"
  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0"/>
  <path d="M12 18v3"/></svg>`;

const STATUS: Record<WidgetState, string> = {
  idle: "Tap the mic or type a question",
  connecting: "Connecting…",
  listening: "Listening… tap again when you’re done",
  thinking: "Thinking…",
  speaking: "Speaking… tap the mic to interrupt",
  confirm: "Waiting for your confirmation",
  done: "Ask another question",
};

const UNAVAILABLE: Record<string, string> = {
  budget: "Voice is paused for today. You can still type your question.",
  no_provider: "Voice isn’t set up on this server yet. You can type your question.",
  unavailable: "Voice is unavailable right now. You can type your question.",
};

function mount(): VoiceServeApi {
  const config = window.VoiceServeConfig ?? {};
  const sessionEndpoint = config.sessionEndpoint ?? "/api/voice/session";
  const textEndpoint = config.textEndpoint ?? "/api/voice/text";

  const host = document.createElement("div");
  host.id = HOST_ID;
  const root = host.attachShadow({ mode: "open" });
  root.innerHTML = `
    <style>${STYLES}</style>
    <button class="fab" type="button" aria-label="Open VoiceServe voice assistant"
      aria-expanded="false" aria-controls="vs-panel">${MIC_ICON}</button>
    <section id="vs-panel" class="panel" role="dialog" aria-label="VoiceServe assistant" hidden>
      <header>
        <div><div class="title">VoiceServe</div>
          <div class="status" role="status" aria-live="polite"></div></div>
        <button class="close" type="button" aria-label="Close">&times;</button>
      </header>
      <div class="log" aria-live="polite"></div>
      <footer>
        <button class="mic" type="button" aria-label="Start speaking">${MIC_ICON}</button>
        <form>
          <input name="q" type="text" maxlength="500" autocomplete="off"
            placeholder="Type a question…" aria-label="Type a question">
          <button class="send" type="submit">Send</button>
        </form>
      </footer>
    </section>`;
  document.body.appendChild(host);

  const fab = root.querySelector<HTMLButtonElement>(".fab")!;
  const panel = root.querySelector<HTMLElement>(".panel")!;
  const status = root.querySelector<HTMLElement>(".status")!;
  const log = root.querySelector<HTMLElement>(".log")!;
  const mic = root.querySelector<HTMLButtonElement>(".mic")!;
  const form = root.querySelector<HTMLFormElement>("form")!;
  const input = root.querySelector<HTMLInputElement>("input")!;
  const send = root.querySelector<HTMLButtonElement>(".send")!;
  const closeButton = root.querySelector<HTMLButtonElement>(".close")!;

  let state: WidgetState = "idle";
  let session: Session | null = null;
  let voice: VoiceClient | null = null;
  let userTurnActive = false;
  const bubbles = new Map<string, HTMLElement>();

  function setState(next: WidgetState) {
    state = next;
    panel.dataset.state = next;
    status.textContent = STATUS[next];
    const live = next === "listening";
    mic.dataset.live = String(live);
    fab.dataset.live = String(live);
    mic.setAttribute("aria-label", live ? "Stop speaking" : next === "speaking" ? "Interrupt and speak" : "Start speaking");
    send.disabled = next === "thinking" || next === "connecting";
    // A late "done" tap after the agent heard the pause itself must not barge in on the answer.
    mic.disabled = next === "thinking";
  }

  function scroll() {
    log.scrollTop = log.scrollHeight;
  }

  function note(text: string, error = false) {
    const p = document.createElement("p");
    p.className = error ? "note error" : "note";
    p.textContent = text;
    log.append(p);
    scroll();
  }

  function bubble(who: "user" | "agent", key: string, text: string, interim = false) {
    let node = bubbles.get(key);
    if (!node) {
      node = document.createElement("p");
      bubbles.set(key, node);
      log.append(node);
    }
    node.className = `bubble ${who}${interim ? " interim" : ""}`;
    node.textContent = text;
    scroll();
  }

  function card(data: unknown) {
    log.append(renderCard(data as Card));
    scroll();
  }

  async function ensureSession(): Promise<Session | null> {
    if (session) return session;
    const res = await fetch(sessionEndpoint, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ page_id: location.pathname }),
    }).catch(() => null);
    if (!res || !res.ok) {
      note(
        res?.status === 401
          ? "Please log in to the portal to use the assistant."
          : "The assistant is unavailable right now. Please try again later.",
        true,
      );
      return null;
    }
    session = (await res.json()) as Session;
    if (!session.voice) {
      mic.disabled = true;
      note(UNAVAILABLE[session.voice_unavailable_reason ?? "unavailable"] ?? UNAVAILABLE.unavailable!);
    }
    return session;
  }

  // --- typed questions ------------------------------------------------------------------

  async function ask(text: string, retried = false): Promise<void> {
    const s = await ensureSession();
    if (!s) return;
    const turn = crypto.getRandomValues(new Uint32Array(1))[0]!.toString(36);
    if (!retried) bubble("user", `t-${turn}`, text);
    setState("thinking");
    const res = await fetch(textEndpoint, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: s.session_id, text, page_id: location.pathname }),
    }).catch(() => null);
    if (res?.status === 404 && !retried) {
      session = null; // expired; start a new one once
      return ask(text, true);
    }
    if (!res || !res.ok || !res.body) {
      note("Sorry, I couldn’t answer that just now. Please try again.", true);
      setState("done");
      return;
    }
    const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffered = "";
    let answer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffered += value;
      let newline: number;
      while ((newline = buffered.indexOf("\n")) >= 0) {
        const line = buffered.slice(0, newline).trim();
        buffered = buffered.slice(newline + 1);
        if (!line) continue;
        const event = JSON.parse(line) as { type: string; text?: string; card?: unknown };
        if (event.type === "sentence" && event.text) {
          answer = answer ? `${answer} ${event.text}` : event.text;
          bubble("agent", `a-${turn}`, answer);
        } else if (event.type === "card") {
          card(event.card);
        }
      }
    }
    setState("done");
  }

  // --- voice -----------------------------------------------------------------------------

  function onAgentState(agentState: AgentState) {
    if (agentState === "thinking") setState("thinking");
    else if (agentState === "speaking") setState("speaking");
    else if (agentState === "listening" && !userTurnActive && (state === "speaking" || state === "thinking")) {
      setState("done");
      void voice?.micOff(); // the mic is only live while the student talks or might interrupt
    }
  }

  async function connectVoice(s: Session): Promise<VoiceClient | null> {
    if (voice?.connected) return voice;
    if (!s.voice) return null;
    setState("connecting");
    const client = new VoiceClient(root, {
      agentState: onAgentState,
      transcript(who, segment, text, final) {
        if (who === "user") {
          userTurnActive = !final;
          bubble("user", `u-${segment}`, text, !final);
          if (final && state === "listening") setState("thinking");
        } else {
          bubble("agent", `a-${segment}`, text);
        }
      },
      card,
      disconnected() {
        voice = null;
        if (state !== "idle") setState("done");
      },
    });
    try {
      await client.connect(s.voice.url, s.voice.token);
    } catch {
      note("Couldn’t connect voice. You can type your question instead.", true);
      setState("idle");
      return null;
    }
    voice = client;
    return client;
  }

  async function toggleTalk() {
    const s = await ensureSession();
    if (!s || !s.voice) return;
    const client = await connectVoice(s);
    if (!client) return;
    try {
      if (state === "listening") {
        userTurnActive = false;
        setState("thinking");
        if (!(await client.endTurn())) {
          note("I didn’t catch that. Tap the mic and try again.");
          setState("done");
          void client.micOff();
        }
      } else {
        userTurnActive = true; // also a barge-in when the agent is speaking
        await client.startTurn();
        setState("listening");
      }
    } catch {
      userTurnActive = false;
      note("The microphone couldn’t start. Check the browser’s permission, or type instead.", true);
      setState("idle");
    }
  }

  // --- panel -----------------------------------------------------------------------------

  const setOpen = (open: boolean) => {
    panel.hidden = !open;
    fab.setAttribute("aria-expanded", String(open));
    if (!open && state === "listening") void voice?.cancelTurn().then(() => setState("idle"));
  };

  fab.addEventListener("click", async () => {
    if (!panel.hidden) return setOpen(false);
    setOpen(true);
    const s = await ensureSession();
    if (s?.voice) await toggleTalk(); // voice first: tapping the mic starts listening
    else input.focus();
  });
  mic.addEventListener("click", () => void toggleTalk());
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text || send.disabled) return;
    input.value = "";
    void ask(text);
  });
  closeButton.addEventListener("click", () => {
    setOpen(false);
    fab.focus();
  });
  root.addEventListener("keydown", (event) => {
    if ((event as KeyboardEvent).key === "Escape" && !panel.hidden) {
      setOpen(false);
      fab.focus();
    }
  });

  setState("idle");
  return { version: VERSION, open: () => setOpen(true), close: () => setOpen(false) };
}

function init(): void {
  if (window.VoiceServe || document.getElementById(HOST_ID)) return;
  window.VoiceServe = mount();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
  init();
}
