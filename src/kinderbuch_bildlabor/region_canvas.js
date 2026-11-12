const NS = "http://www.w3.org/2000/svg";
const memory = {};
const COLORS = { illustration: "#1f77b4", text: "#2ca02c" };

function el(name, attrs = {}) {
  const node = document.createElementNS(NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  return node;
}

const same = (a, b) => a.every((value, index) => value === b[index]);

export default function (component) {
  const { data, parentElement, setStateValue } = component;
  const W = data.width;
  const H = data.height;
  const mem = (memory[data.instance] ??= { selected: new Set(), mode: "select", focus: null });
  const rects = data.regions.map((r) => ({ ...r, xywh: r.xywh.slice() }));
  let created = data.created ? { type: data.created.type, xywh: data.created.xywh.slice() } : null;

  parentElement.replaceChildren();
  const bar = document.createElement("div");
  bar.style.cssText = "display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px;font:14px sans-serif";
  const modes = [
    ["select", "Auswählen und verschieben"],
    ["illustration", "Illustration zeichnen"],
    ["text", "Text zeichnen"],
  ];
  for (const [value, text] of modes) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text;
    button.setAttribute("aria-pressed", String(mem.mode === value));
    button.style.cssText = `padding:4px 8px;cursor:pointer;${mem.mode === value ? "font-weight:bold;outline:2px solid #1f77b4" : ""}`;
    button.onclick = () => {
      mem.mode = value;
      bar.querySelectorAll("button").forEach((b) => {
        const on = b === button;
        b.setAttribute("aria-pressed", String(on));
        b.style.cssText = `padding:4px 8px;cursor:pointer;${on ? "font-weight:bold;outline:2px solid #1f77b4" : ""}`;
      });
    };
    bar.append(button);
  }
  const hint = document.createElement("span");
  hint.style.cssText = "align-self:center;color:#555";
  hint.textContent = "Umschalt+Klick: mehrere wählen. Pfeiltasten verschieben (Umschalt = 10 px), Alt+Pfeil ändert Breite/Höhe.";
  bar.append(hint);

  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "group", "aria-label": "Zeichenfläche mit Regionen auf dem Scan" });
  svg.style.cssText = "width:100%;max-height:75vh;touch-action:none;background:#eee;display:block";
  svg.append(el("image", { href: data.image, width: W, height: H }));
  const layer = el("g");
  svg.append(layer);
  parentElement.append(bar, svg);

  const unit = Math.max(W, H) / 200;

  function point(event) {
    const p = svg.createSVGPoint();
    p.x = event.clientX;
    p.y = event.clientY;
    const q = p.matrixTransform(svg.getScreenCTM().inverse());
    return [Math.round(q.x), Math.round(q.y)];
  }

  function emit() {
    const changes = rects.filter((r) => !same(r.xywh, r.saved)).map((r) => ({ id: r.id, xywh: r.xywh }));
    setStateValue("edit", { seq: `${Date.now()}-${Math.random()}`, changes, created });
  }

  function clampMove(base, dx, dy) {
    const [x, y, w, h] = base;
    return [Math.min(Math.max(x + dx, 0), W - w), Math.min(Math.max(y + dy, 0), H - h), w, h];
  }

  function draw() {
    layer.replaceChildren();
    rects.forEach((r, index) => {
      const [x, y, w, h] = r.xywh;
      const chosen = mem.selected.has(r.id);
      const color = COLORS[r.type] ?? "#d62728";
      const group = el("g");
      const box = el("rect", {
        x, y, width: w, height: h, fill: color, "fill-opacity": chosen ? 0.25 : 0.1,
        stroke: color, "stroke-width": unit * (chosen ? 1.2 : 0.7), tabindex: 0, role: "button",
        "aria-pressed": String(chosen), "data-id": r.id,
        "aria-label": `Region ${index + 1}, ${r.label}: x ${x}, y ${y}, Breite ${w}, Höhe ${h}`,
      });
      box.style.cursor = "move";
      box.addEventListener("keydown", (event) => onKey(event, r));
      box.addEventListener("focus", () => (mem.focus = r.id));
      group.append(box);
      const label = el("text", { x: x + unit, y: y + unit * 4, "font-size": unit * 3.5, fill: "#000", stroke: "#fff", "stroke-width": unit * 0.6, "paint-order": "stroke" });
      label.textContent = `${index + 1} ${r.label}`;
      label.style.pointerEvents = "none";
      group.append(label);
      if (chosen) {
        for (const [cx, cy, corner] of [[x, y, "nw"], [x + w, y, "ne"], [x, y + h, "sw"], [x + w, y + h, "se"]]) {
          const handle = el("rect", { x: cx - unit * 1.5, y: cy - unit * 1.5, width: unit * 3, height: unit * 3, fill: "#fff", stroke: color, "stroke-width": unit * 0.5, "data-handle": corner, "data-id": r.id });
          handle.style.cursor = `${corner}-resize`;
          group.append(handle);
        }
      }
      layer.append(group);
    });
    if (created) {
      const [x, y, w, h] = created.xywh;
      layer.append(el("rect", { x, y, width: w, height: h, fill: "none", stroke: "#d62728", "stroke-width": unit * 0.8, "stroke-dasharray": `${unit * 2} ${unit * 1.5}` }));
    }
    if (mem.focus) layer.querySelector(`[data-id="${CSS.escape(mem.focus)}"][role="button"]`)?.focus({ preventScroll: true });
  }

  function onKey(event, r) {
    const step = event.shiftKey ? 10 : 1;
    const delta = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[event.key];
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (!event.shiftKey) mem.selected.clear();
      mem.selected.has(r.id) ? mem.selected.delete(r.id) : mem.selected.add(r.id);
      draw();
      return;
    }
    if (!delta) return;
    event.preventDefault();
    const targets = mem.selected.has(r.id) ? rects.filter((t) => mem.selected.has(t.id)) : [r];
    if (event.altKey) {
      for (const t of targets) {
        const [x, y, w, h] = t.xywh;
        t.xywh = [x, y, Math.max(1, Math.min(w + delta[0], W - x)), Math.max(1, Math.min(h + delta[1], H - y))];
      }
    } else {
      const dx = Math.max(Math.max(...targets.map((t) => -t.xywh[0])), Math.min(Math.min(...targets.map((t) => W - t.xywh[0] - t.xywh[2])), delta[0]));
      const dy = Math.max(Math.max(...targets.map((t) => -t.xywh[1])), Math.min(Math.min(...targets.map((t) => H - t.xywh[1] - t.xywh[3])), delta[1]));
      for (const t of targets) t.xywh = [t.xywh[0] + dx, t.xywh[1] + dy, t.xywh[2], t.xywh[3]];
    }
    draw();
    emit();
  }

  let op = null;
  svg.addEventListener("pointerdown", (event) => {
    const start = point(event);
    const id = event.target.getAttribute("data-id");
    const handle = event.target.getAttribute("data-handle");
    if (handle) {
      const r = rects.find((t) => t.id === id);
      op = { kind: "resize", r, handle, base: r.xywh.slice() };
    } else if (mem.mode !== "select") {
      op = { kind: "draw", type: mem.mode, start };
    } else if (id) {
      if (event.shiftKey) {
        mem.selected.has(id) ? mem.selected.delete(id) : mem.selected.add(id);
      } else if (!mem.selected.has(id)) {
        mem.selected = new Set([id]);
      }
      mem.focus = id;
      op = mem.selected.has(id) ? { kind: "move", bases: rects.filter((t) => mem.selected.has(t.id)).map((t) => [t, t.xywh.slice()]) } : null;
    } else {
      if (!event.shiftKey) mem.selected.clear();
      op = null;
    }
    if (op) op.start = start;
    if (op) svg.setPointerCapture(event.pointerId);
    event.preventDefault();
    draw();
  });

  svg.addEventListener("pointermove", (event) => {
    if (!op) return;
    const [px, py] = point(event);
    const [sx, sy] = op.start;
    if (op.kind === "move") {
      const dx = Math.max(Math.max(...op.bases.map(([, b]) => -b[0])), Math.min(Math.min(...op.bases.map(([, b]) => W - b[0] - b[2])), px - sx));
      const dy = Math.max(Math.max(...op.bases.map(([, b]) => -b[1])), Math.min(Math.min(...op.bases.map(([, b]) => H - b[1] - b[3])), py - sy));
      for (const [t, b] of op.bases) t.xywh = clampMove(b, dx, dy);
    } else {
      const cx = Math.min(Math.max(px, 0), W);
      const cy = Math.min(Math.max(py, 0), H);
      let ax = sx;
      let ay = sy;
      if (op.kind === "resize") {
        const [x, y, w, h] = op.base;
        ax = op.handle.includes("w") ? x + w : x;
        ay = op.handle.includes("n") ? y + h : y;
      }
      const box = [Math.min(ax, cx), Math.min(ay, cy), Math.max(1, Math.abs(cx - ax)), Math.max(1, Math.abs(cy - ay))];
      box[2] = Math.min(box[2], W - box[0]);
      box[3] = Math.min(box[3], H - box[1]);
      if (op.kind === "resize") op.r.xywh = box;
      else created = { type: op.type, xywh: box };
    }
    draw();
  });

  const finish = () => {
    if (!op) return;
    const changed = op.kind !== "move" || op.bases.some(([t, b]) => !same(t.xywh, b));
    op = null;
    if (changed) emit();
  };
  svg.addEventListener("pointerup", finish);
  svg.addEventListener("pointercancel", finish);

  draw();
}
