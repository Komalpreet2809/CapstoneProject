// On-screen cards for spoken answers (brief: every spoken answer also renders a card).
// Built with DOM APIs and textContent only: card data never becomes HTML.

export type CardRow = {
  code: string;
  title: string;
  attended: number;
  held: number;
  percent: number | null;
  status: "ok" | "warn" | "low" | "none";
  hint: string;
};

export type Card =
  | {
      kind: "attendance";
      title: string;
      summary: string;
      rows: CardRow[];
      highlight: string | null;
      link?: { href: string; label: string };
    }
  | {
      kind: "list";
      title: string;
      summary: string;
      items: ListItem[];
      link?: { href: string; label: string };
    }
  | { kind: "message"; title: string; body: string; link?: { href: string; label: string } };

export type ListItem = {
  label: string;
  value: string;
  note: string;
  status: "ok" | "warn" | "low" | "none";
};

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/** Links stay on the host site: only same-origin relative paths are followed. */
function safeHref(href: string): string | null {
  return /^\/(?![/\\])/.test(href) ? href : null;
}

export function renderCard(card: Card): HTMLElement {
  const box = el("section", "card");
  box.setAttribute("aria-label", card.title);
  box.append(el("h3", undefined, card.title));
  if (card.kind === "attendance") {
    box.append(el("p", undefined, card.summary));
    const list = el("ul");
    for (const row of card.rows) {
      const item = el("li", row.code === card.highlight ? "hl" : undefined);
      item.append(
        el("span", "code", row.code),
        el("span", "pct " + row.status, row.percent === null ? "–" : `${row.percent}%`),
        el("span", "name", row.title),
        el("span", "hint", `${row.attended}/${row.held} attended · ${row.hint}`),
      );
      list.append(item);
    }
    box.append(list);
  } else if (card.kind === "list") {
    box.append(el("p", undefined, card.summary));
    if (card.items.length > 0) {
      const list = el("ul", "items");
      for (const item of card.items) {
        const li = el("li");
        li.append(
          el("span", "code", item.label),
          el("span", "pct " + item.status, item.value),
          el("span", "hint", item.note),
        );
        list.append(li);
      }
      box.append(list);
    }
  } else {
    box.append(el("p", undefined, card.body));
  }
  const href = card.link ? safeHref(card.link.href) : null;
  if (card.link && href) {
    const a = el("a", undefined, card.link.label);
    a.href = href;
    box.append(a);
  }
  return box;
}
