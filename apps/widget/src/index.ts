/**
 * VoiceServe widget: the floating mic button and panel embedded on every Mini UMS page.
 *
 * Shipped as one framework-free script. Markup and styles live in a shadow root so the host
 * page and the widget cannot break each other's CSS. M1 renders the button and panel only;
 * push-to-talk, live captions, answer cards, confirm cards and the text fallback arrive in
 * M3–M4.
 */

export type WidgetState = "idle" | "listening" | "thinking" | "speaking" | "confirm" | "done";

export interface VoiceServeApi {
  version: string;
  open(): void;
  close(): void;
}

declare global {
  interface Window {
    VoiceServe?: VoiceServeApi;
  }
}

const VERSION = "0.1.0";
const HOST_ID = "voiceserve-widget";

const MIC_ICON = `<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true" fill="none"
  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0"/>
  <path d="M12 18v3"/></svg>`;

const STYLES = `
  :host { all: initial; }
  * { box-sizing: border-box; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  .fab {
    position: fixed; right: 20px; bottom: 20px; z-index: 2147483000;
    width: 60px; height: 60px; border-radius: 50%; border: 0; cursor: pointer;
    display: grid; place-items: center; color: #fff; background: #0f766e;
    box-shadow: 0 6px 20px rgb(0 0 0 / 0.25);
  }
  .fab:hover { background: #115e59; }
  .fab:focus-visible { outline: 3px solid #f59e0b; outline-offset: 3px; }
  .panel {
    position: fixed; right: 20px; bottom: 92px; z-index: 2147483000;
    width: 360px; max-height: 70vh; overflow: auto;
    border-radius: 14px; background: #fff; color: #1c1917;
    box-shadow: 0 12px 40px rgb(0 0 0 / 0.25);
  }
  .panel[hidden] { display: none; }
  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 16px; border-bottom: 1px solid #e7e5e4; font-weight: 600;
  }
  .close {
    border: 0; background: none; font-size: 22px; line-height: 1; cursor: pointer; color: #57534e;
  }
  .body { padding: 16px; font-size: 14px; line-height: 1.5; color: #44403c; }
  @media (max-width: 640px) {
    .panel { left: 0; right: 0; bottom: 0; width: auto; border-radius: 16px 16px 0 0; }
    .fab { right: 16px; bottom: 16px; }
  }
`;

function mount(): VoiceServeApi {
  const host = document.createElement("div");
  host.id = HOST_ID;
  const root = host.attachShadow({ mode: "open" });
  root.innerHTML = `
    <style>${STYLES}</style>
    <button class="fab" type="button" aria-label="Open VoiceServe voice assistant"
      aria-expanded="false" aria-controls="vs-panel">${MIC_ICON}</button>
    <section id="vs-panel" class="panel" role="dialog" aria-label="VoiceServe" hidden>
      <header><span>VoiceServe</span>
        <button class="close" type="button" aria-label="Close">&times;</button></header>
      <div class="body" data-state="idle">
        Voice assistant preview. Speaking and typing to the assistant arrive in milestone M3.
      </div>
    </section>`;
  document.body.appendChild(host);

  const fab = root.querySelector<HTMLButtonElement>(".fab")!;
  const panel = root.querySelector<HTMLElement>(".panel")!;
  const closeButton = root.querySelector<HTMLButtonElement>(".close")!;

  const setOpen = (open: boolean) => {
    panel.hidden = !open;
    fab.setAttribute("aria-expanded", String(open));
    if (open) closeButton.focus();
  };

  fab.addEventListener("click", () => setOpen(panel.hidden));
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
