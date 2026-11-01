// All widget CSS lives in the shadow root, so the host page and the widget can't affect
// each other. Colours are the widget's own, readable on any host page.
export const STYLES = `
  :host { all: initial; }
  * { box-sizing: border-box; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  button { font: inherit; }
  .fab {
    position: fixed; right: 20px; bottom: 20px; z-index: 2147483000;
    width: 60px; height: 60px; border-radius: 50%; border: 0; cursor: pointer;
    display: grid; place-items: center; color: #fff; background: #0f766e;
    box-shadow: 0 6px 20px rgb(0 0 0 / 0.25); transition: transform .15s;
  }
  .fab:hover { background: #115e59; }
  .fab:focus-visible, .mic:focus-visible, .send:focus-visible, input:focus-visible {
    outline: 3px solid #f59e0b; outline-offset: 2px;
  }
  .fab[data-live="true"] { background: #b91c1c; animation: pulse 1.4s ease-in-out infinite; }
  @keyframes pulse { 50% { transform: scale(1.06); } }
  @media (prefers-reduced-motion: reduce) { .fab[data-live="true"] { animation: none; } }

  .panel {
    position: fixed; right: 20px; bottom: 92px; z-index: 2147483000;
    width: 380px; height: min(560px, 75vh); display: flex; flex-direction: column;
    border-radius: 16px; background: #fff; color: #1c1917; overflow: hidden;
    box-shadow: 0 12px 40px rgb(0 0 0 / 0.25);
  }
  .panel[hidden] { display: none; }
  header {
    display: flex; align-items: center; gap: 10px; padding: 12px 14px;
    background: #134e4a; color: #fff;
  }
  header .title { font-weight: 700; font-size: 15px; }
  header .status { font-size: 12px; color: #ccfbf1; }
  header .close {
    margin-left: auto; border: 0; background: none; color: #ccfbf1; font-size: 24px;
    line-height: 1; cursor: pointer; padding: 0 4px;
  }
  .log { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 10px;
    background: #f5f5f4; font-size: 14px; line-height: 1.45; }
  .bubble { max-width: 85%; padding: 8px 12px; border-radius: 14px; white-space: pre-wrap; }
  .bubble.user { align-self: flex-end; background: #0f766e; color: #fff; border-bottom-right-radius: 4px; }
  .bubble.user.interim { opacity: .7; font-style: italic; }
  .bubble.agent { align-self: flex-start; background: #fff; color: #292524;
    border: 1px solid #e7e5e4; border-bottom-left-radius: 4px; }
  .note { align-self: center; font-size: 12px; color: #57534e; text-align: center; }
  .note.error { color: #b91c1c; }

  .card { align-self: stretch; background: #fff; border: 1px solid #d6d3d1; border-radius: 12px;
    padding: 12px; }
  .card h3 { margin: 0 0 4px; font-size: 14px; color: #134e4a; }
  .card p { margin: 0 0 8px; color: #44403c; }
  .card ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  .card li { display: grid; grid-template-columns: 1fr auto; gap: 2px 8px; padding: 6px 8px;
    border-radius: 8px; background: #fafaf9; }
  .card li.hl { outline: 2px solid #f59e0b; background: #fffbeb; }
  .card .code { font-weight: 700; font-size: 12px; color: #0f766e; }
  .card .name { grid-column: 1; font-size: 13px; color: #292524; }
  .card .pct { grid-row: 1 / span 2; grid-column: 2; align-self: center; font-weight: 800; font-size: 16px; }
  .card .hint { grid-column: 1 / span 2; font-size: 12px; color: #57534e; }
  .pct.low { color: #be123c; } .pct.warn { color: #b45309; } .pct.ok { color: #047857; } .pct.none { color: #78716c; }
  .card a { display: inline-block; margin-top: 8px; font-size: 13px; font-weight: 600; color: #0f766e; }

  footer { display: flex; align-items: center; gap: 8px; padding: 10px; border-top: 1px solid #e7e5e4; }
  form { flex: 1; display: flex; gap: 6px; }
  input { flex: 1; min-width: 0; padding: 9px 12px; border: 1px solid #d6d3d1; border-radius: 999px;
    font-size: 14px; color: #1c1917; background: #fff; }
  .send { border: 0; border-radius: 999px; padding: 0 14px; background: #e7e5e4; color: #292524;
    font-weight: 600; cursor: pointer; }
  .send:disabled { opacity: .5; cursor: default; }
  .mic { width: 44px; height: 44px; flex: none; border-radius: 50%; border: 0; cursor: pointer;
    display: grid; place-items: center; background: #0f766e; color: #fff; }
  .mic:disabled { background: #a8a29e; cursor: not-allowed; }
  .mic[data-live="true"] { background: #b91c1c; }

  @media (max-width: 640px) {
    .panel { left: 0; right: 0; bottom: 0; width: auto; height: 70vh; border-radius: 18px 18px 0 0; }
    .fab { right: 16px; bottom: 16px; }
  }
`;
