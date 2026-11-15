const NS = "http://www.w3.org/2000/svg";
const memory = {};

function el(name, attrs = {}) {
  const node = document.createElementNS(NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  return node;
}

const same = (a, b) => a.every((value, index) => value === b[index]);

// Etikettenschrift weiß oder fast schwarz, je nachdem welche auf der Regionsfarbe 4,5:1 erreicht
function inkOn(hex) {
  const lin = (v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  const [r, g, b] = [1, 3, 5].map((i) => lin(parseInt(hex.slice(i, i + 2), 16) / 255));
  const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return 1.05 / (lum + 0.05) >= 4.5 ? "#fff" : "#15181C";
}

const STYLE = `
.blc-bar { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; }
.blc-bar .blc-seg:last-child { order: 3; }
.blc-spacer { flex: 1; }
.blc-bar details { font-size: 0.875rem; color: var(--bl-ink-muted); }
.blc-seg { display: inline-flex; border: 1px solid var(--bl-border-strong); border-radius: 0.625rem; overflow: hidden; background: var(--bl-surface); }
.blc-seg button, .blc-look button {
  font: inherit; font-size: 0.875rem; font-weight: 500; color: var(--bl-ink); background: transparent;
  border: 0; padding: 0.45rem 0.8rem; min-height: 2.5rem; min-width: 2.5rem; cursor: pointer;
}
.blc-seg button + button { border-left: 1px solid var(--bl-border); }
.blc-seg button:hover { background: var(--bl-primary-tint); }
.blc-seg button[aria-pressed="true"] { background: var(--bl-primary-tint); color: var(--bl-primary); font-weight: 620; box-shadow: inset 0 -2px 0 var(--bl-primary); }
.blc-look button { border: 1px solid var(--bl-border-strong); border-radius: 0.625rem; background: var(--bl-surface); }
.blc-bar button:focus-visible, .blc-bar summary:focus-visible, .blc-bar input:focus-visible, .blc-look button:focus-visible {
  outline: 3px solid var(--bl-primary); outline-offset: 2px;
}
.blc-bar details { border: 1px solid var(--bl-border); border-radius: 0.625rem; background: var(--bl-surface); padding: 0.4rem 0.75rem; }
.blc-bar details[open] { flex-basis: 100%; order: 5; }
.blc-bar summary { cursor: pointer; color: var(--bl-ink); font-weight: 500; }
.blc-bar details p { margin: 0.35rem 0 0; }
.blc-look { display: flex; flex-wrap: wrap; gap: 0.75rem 1.25rem; align-items: center; padding-top: 0.5rem; }
.blc-look input { accent-color: var(--bl-primary); vertical-align: middle; }
.blc-svg { width: 100%; height: clamp(18rem, calc(100vh - 28rem), 42rem); touch-action: none; background: var(--bl-mat, #e2e3e1); display: block; border-radius: 0.875rem; }
.blc-svg text { font-family: "Geist Mono", ui-monospace, monospace; }
.blc-svg[data-mode="select"] [role="button"] { cursor: move; }
.blc-svg[data-mode="illustration"], .blc-svg[data-mode="text"] { cursor: crosshair; }
.blc-svg:focus-visible, .blc-svg [role="button"]:focus-visible { outline: 3px solid var(--bl-primary); outline-offset: 2px; }
.blc-status { margin: 0.4rem 0 0; font-size: 0.8125rem; color: var(--bl-ink-muted); font-variant-numeric: tabular-nums; }
.blc-short { display: none; }
@media (min-height: 1001px) { .blc-svg { height: clamp(18rem, calc(100vh - 38rem), 42rem); } }
@media (max-width: 1400px) {
  .blc-long { display: none; }
  .blc-short { display: inline; }
}
.blc-seg button { white-space: nowrap; }
@media (max-width: 640px) {
  .blc-bar > .blc-seg { width: 100%; }
  .blc-seg button { flex: 1 1 0; min-height: 2.75rem; padding-inline: 0.4rem; }
  .blc-long { display: none; }
  .blc-short { display: inline; }
  .blc-spacer { display: none; }
  .blc-bar details { flex: 1 1 40%; }
}
`;


export default function (component) {
  const { data, parentElement, setStateValue } = component;
  const W = data.width;
  const typeColor = (type) => data.colors[type] ?? data.colors.other;
  const H = data.height;
  const mem = (memory[data.instance] ??= { selected: new Set(), mode: "select", focus: null, view: { x: 0, y: 0, w: W }, fitted: false, look: { brightness: 100, contrast: 100, gray: false, invert: false, labels: true } });
  const rects = data.regions.map((r) => ({ ...r, xywh: r.xywh.slice() }));
  let created = data.created ? { type: data.created.type, xywh: data.created.xywh.slice() } : null;

  parentElement.replaceChildren();
  const style = document.createElement("style");
  style.textContent = STYLE;

  const button = (text, label, onclick) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = text;
    if (label) b.setAttribute("aria-label", label);
    b.onclick = onclick;
    return b;
  };

  const bar = document.createElement("div");
  bar.className = "blc-bar";
  const modeGroup = document.createElement("div");
  modeGroup.className = "blc-seg";
  modeGroup.setAttribute("role", "group");
  modeGroup.setAttribute("aria-label", "Werkzeug");
  const modes = [
    ["select", "Auswählen und verschieben", "Auswählen"],
    ["illustration", "Illustration zeichnen", "Illustration"],
    ["text", "Text zeichnen", "Text"],
  ];
  for (const [value, text, short] of modes) {
    const b = button(text, null, () => {
      mem.mode = value;
      svg.dataset.mode = value;
      modeGroup.querySelectorAll("button").forEach((other) => other.setAttribute("aria-pressed", String(other === b)));
    });
    b.setAttribute("aria-pressed", String(mem.mode === value));
    b.innerHTML = `<span class="blc-long"></span><span class="blc-short"></span>`;
    b.querySelector(".blc-long").textContent = text;
    b.querySelector(".blc-short").textContent = short;
    b.setAttribute("aria-label", text);
    modeGroup.append(b);
  }
  const zoomGroup = document.createElement("div");
  zoomGroup.className = "blc-seg";
  zoomGroup.setAttribute("role", "group");
  zoomGroup.setAttribute("aria-label", "Ansicht");
  zoomGroup.append(
    button("−", "Verkleinern (Taste -)", () => zoomAt(0.8, ...centre())),
    button("+", "Vergrößern (Taste +)", () => zoomAt(1.25, ...centre())),
    button("Gesamtansicht", "Gesamtansicht (Taste 0)", () => {
      Object.assign(view, { x: 0, y: 0, w: fullW() });
      applyView();
      draw();
    }),
  );
  const spacer = document.createElement("span");
  spacer.className = "blc-spacer";
  bar.append(modeGroup, spacer, zoomGroup);

  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, tabindex: 0, role: "group", "aria-label": "Zeichenfläche mit Regionen auf dem Scan" });
  svg.classList.add("blc-svg");
  svg.dataset.mode = mem.mode;
  const picture = el("image", { href: data.image, width: W, height: H });
  svg.append(picture);
  const layer = el("g");
  svg.append(layer);
  const status = document.createElement("p");
  status.className = "blc-status";
  status.setAttribute("aria-live", "polite");

  const view = mem.view;
  const unitNow = () => (Math.max(W, H) / 200) * (view.w / W);

  // Seitenverhältnis der Zeichenfläche: der Ausschnitt füllt sie, statt die Scanseite zu umranden
  let ar = H / W;
  const measure = () => {
    const r = svg.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return false;
    ar = r.height / r.width;
    return true;
  };
  const fullW = () => Math.max(W, H / ar);
  const within = (v, size, total) => (size >= total ? (total - size) / 2 : Math.min(Math.max(v, 0), total - size));

  function clampView() {
    measure();
    view.w = Math.min(fullW(), Math.max(W / 20, view.w));
    view.x = within(view.x, view.w, W);
    view.y = within(view.y, view.w * ar, H);
  }

  // Erster Blick: die Regionen füllen die Fläche; „Gesamtansicht“ zeigt die ganze Seite
  function fitRegions() {
    measure();
    if (!rects.length) return Object.assign(view, { x: 0, y: 0, w: fullW() });
    const x0 = Math.min(...rects.map((r) => r.xywh[0])), y0 = Math.min(...rects.map((r) => r.xywh[1]));
    const x1 = Math.max(...rects.map((r) => r.xywh[0] + r.xywh[2])), y1 = Math.max(...rects.map((r) => r.xywh[1] + r.xywh[3]));
    const w = Math.max((x1 - x0) * 1.12, ((y1 - y0) * 1.12) / ar);
    Object.assign(view, { w, x: (x0 + x1) / 2 - w / 2, y: (y0 + y1) / 2 - (w * ar) / 2 });
  }

  function applyView() {
    clampView();
    svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.w} ${view.w * ar}`);
  }

  function zoomAt(factor, cx, cy) {
    const next = Math.min(fullW(), Math.max(W / 20, view.w / factor));
    const k = next / view.w;
    view.x = cx - (cx - view.x) * k;
    view.y = cy - (cy - view.y) * k;
    view.w = next;
    applyView();
    draw();
  }

  const centre = () => [view.x + view.w / 2, view.y + (view.w * ar) / 2];

  function applyLook() {
    const l = mem.look;
    picture.style.filter = `brightness(${l.brightness}%) contrast(${l.contrast}%) grayscale(${l.gray ? 1 : 0}) invert(${l.invert ? 1 : 0})`;
  }

  // Bildanpassung und Bedienhilfe aufklappbar: sichtbar auf Wunsch, ohne die Zeichenfläche zu verdrängen
  const lookBox = document.createElement("details");
  lookBox.innerHTML = "<summary>Bildanpassung</summary>";
  const look = document.createElement("div");
  look.className = "blc-look";
  for (const [key, text, min, max] of [["brightness", "Helligkeit", 30, 250], ["contrast", "Kontrast", 30, 300]]) {
    const label = document.createElement("label");
    label.textContent = `${text} `;
    const input = document.createElement("input");
    Object.assign(input, { type: "range", min, max, value: mem.look[key] });
    input.oninput = () => {
      mem.look[key] = Number(input.value);
      applyLook();
    };
    label.append(input);
    look.append(label);
  }
  for (const [key, text] of [["gray", "Graustufen"], ["invert", "Invertieren"]]) {
    const label = document.createElement("label");
    const input = document.createElement("input");
    Object.assign(input, { type: "checkbox", checked: mem.look[key] });
    input.onchange = () => {
      mem.look[key] = input.checked;
      applyLook();
    };
    label.append(input, ` ${text}`);
    look.append(label);
  }
  const labelsBox = document.createElement("label");
  const labelsInput = document.createElement("input");
  Object.assign(labelsInput, { type: "checkbox", checked: mem.look.labels });
  labelsInput.onchange = () => {
    mem.look.labels = labelsInput.checked;
    draw();
  };
  labelsBox.append(labelsInput, " Etiketten zeigen");
  look.append(labelsBox);
  look.append(
    button("Ansicht zurücksetzen", null, () => {
      Object.assign(view, { x: 0, y: 0, w: fullW() });
      Object.assign(mem.look, { brightness: 100, contrast: 100, gray: false, invert: false, labels: true });
      applyView();
      applyLook();
      look.querySelectorAll("input").forEach((i) => {
        if (i.type === "range") i.value = 100;
        else i.checked = i === labelsInput;
      });
      draw();
    }),
  );
  const lookNote = document.createElement("p");
  lookNote.textContent = "Die Regler ändern nur die Anzeige, nicht den Scan.";
  lookBox.append(look, lookNote);
  const helpBox = document.createElement("details");
  helpBox.innerHTML = "<summary>Maus und Tastatur</summary>";
  for (const text of [
    "Umschalt+Klick: mehrere wählen. Pfeiltasten verschieben (Umschalt = 10 px), Alt+Pfeil ändert Breite/Höhe.",
    "Ansicht: Mausrad oder +/- zoomt, Ziehen auf leerer Fläche oder Leertaste+Ziehen verschiebt, 0 = Gesamtansicht.",
    "Gestrichelte Rahmen sind noch nicht gespeichert.",
  ]) {
    const line = document.createElement("p");
    line.textContent = text;
    helpBox.append(line);
  }
  bar.insertBefore(helpBox, spacer);
  bar.insertBefore(lookBox, helpBox);
  parentElement.append(style, bar, svg, status);
  // Gemessen wird erst, wenn die Fläche sichtbar ist (verborgene Reiter haben keine Größe)
  const fitOnce = () => {
    if (!mem.fitted && measure()) {
      mem.fitted = true;
      fitRegions();
    }
  };
  fitOnce();
  applyView();
  new ResizeObserver(() => {
    fitOnce();
    applyView();
    draw();
  }).observe(svg);
  applyLook();

  svg.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      const q = pointFloat(event);
      zoomAt(event.deltaY < 0 ? 1.25 : 0.8, q[0], q[1]);
    },
    { passive: false },
  );
  let space = false;
  svg.addEventListener("keydown", (event) => {
    if (event.target === svg && event.key === " ") {
      space = true;
      event.preventDefault();
    } else if (event.key === "+" || event.key === "=") {
      zoomAt(1.25, ...centre());
    } else if (event.key === "-") {
      zoomAt(0.8, ...centre());
    } else if (event.key === "0") {
      Object.assign(view, { x: 0, y: 0, w: fullW() });
      applyView();
      draw();
    }
  });
  svg.addEventListener("keyup", (event) => {
    if (event.key === " ") space = false;
  });

  function pointFloat(event) {
    const p = svg.createSVGPoint();
    p.x = event.clientX;
    p.y = event.clientY;
    const q = p.matrixTransform(svg.getScreenCTM().inverse());
    return [q.x, q.y];
  }

  function point(event) {
    const q = pointFloat(event);
    return [Math.round(q[0]), Math.round(q[1])];
  }

  function emit() {
    const changes = rects.filter((r) => !same(r.xywh, r.saved)).map((r) => ({ id: r.id, xywh: r.xywh }));
    setStateValue("edit", { seq: `${Date.now()}-${Math.random()}`, changes, created });
  }

  function clampMove(base, dx, dy) {
    const [x, y, w, h] = base;
    return [Math.min(Math.max(x + dx, 0), W - w), Math.min(Math.max(y + dy, 0), H - h), w, h];
  }

  // Beschriftung als farbiges Etikett über dem Rahmen (innen, wenn oben kein Platz ist)
  function tag(x, y, h, text, color) {
    // 12 Bildschirmpixel, unabhängig von Scangröße und Zoom
    const size = 12 / (svg.getScreenCTM()?.a || 1);
    const unit = size / 2.4;
    const height = size * 1.6;
    const room = svg.viewBox.baseVal;
    const top = y - height >= room.y ? y - height : y + h + height <= room.y + room.height ? y + h : y;
    const group = el("g", { "pointer-events": "none" });
    group.append(el("rect", { x, y: top, width: text.length * size * 0.58 + size, height, rx: unit * 0.5, fill: color }));
    const label = el("text", { x: x + size * 0.5, y: top + size * 1.15, "font-size": size, "font-weight": 600, fill: inkOn(color) });
    label.textContent = text;
    group.append(label);
    return group;
  }

  function frame(x, y, w, h, color, unit, { chosen = false, dashed = false } = {}) {
    const dash = dashed ? { "stroke-dasharray": `${unit * 2} ${unit * 1.5}` } : {};
    // Weißer Saum außen: Rahmen bleibt auf dunklem Holzschnitt wie auf hellem Papier sichtbar
    return [
      el("rect", { x, y, width: w, height: h, fill: "none", stroke: "#fff", "stroke-opacity": 0.9, "stroke-width": unit * (chosen ? 2.6 : 1.8), "pointer-events": "none" }),
      el("rect", { x, y, width: w, height: h, fill: color, "fill-opacity": chosen ? 0.1 : 0.03, stroke: color, "stroke-width": unit * (chosen ? 1.3 : 0.8), ...dash }),
    ];
  }

  function describe() {
    const chosen = rects.filter((r) => mem.selected.has(r.id));
    const open = rects.filter((r) => !same(r.xywh, r.saved)).length + (created ? 1 : 0);
    const parts = [
      chosen.length
        ? chosen.map((r) => `Region ${rects.indexOf(r) + 1} (${r.label}): x ${r.xywh[0]}, y ${r.xywh[1]}, Breite ${r.xywh[2]}, Höhe ${r.xywh[3]}`).join("; ")
        : "Keine Region gewählt.",
      open ? `${open} ungespeicherte Änderung${open === 1 ? "" : "en"} (gestrichelt); unten speichern.` : "Keine ungespeicherten Änderungen.",
    ];
    const text = parts.join(" · ");
    if (status.textContent !== text) status.textContent = text;
  }

  function draw() {
    const unit = unitNow();
    layer.replaceChildren();
    rects.forEach((r, index) => {
      const [x, y, w, h] = r.xywh;
      const chosen = mem.selected.has(r.id);
      const dirty = !same(r.xywh, r.saved);
      const color = typeColor(r.type);
      const group = el("g");
      const [halo, box] = frame(x, y, w, h, color, unit, { chosen, dashed: dirty });
      Object.entries({
        tabindex: 0, role: "button", "aria-pressed": String(chosen), "data-id": r.id,
        "aria-label": `Region ${index + 1}, ${r.label}: x ${x}, y ${y}, Breite ${w}, Höhe ${h}${dirty ? ", nicht gespeichert" : ""}`,
      }).forEach(([key, value]) => box.setAttribute(key, value));
      box.addEventListener("keydown", (event) => onKey(event, r));
      box.addEventListener("focus", () => (mem.focus = r.id));
      group.append(halo, box);
      if (mem.look.labels || chosen) group.append(tag(x, y, h, `${index + 1} · ${r.label}${dirty ? " · geändert" : ""}`, color));
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
      const color = typeColor(created.type);
      const [halo, box] = frame(x, y, w, h, color, unit, { chosen: true, dashed: true });
      box.setAttribute("pointer-events", "none");
      layer.append(halo, box, tag(x, y, h, `neu · ${created.type === "text" ? "Text" : "Illustration"}`, color));
    }
    describe();
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
    if (!handle && (space || (mem.mode === "select" && !id))) {
      if (!event.shiftKey && !space) mem.selected.clear();
      op = { kind: "pan", client: [event.clientX, event.clientY], base: { x: view.x, y: view.y } };
      svg.setPointerCapture(event.pointerId);
      event.preventDefault();
      draw();
      return;
    }
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
    if (op.kind === "pan") {
      const scale = svg.getScreenCTM().a;
      view.x = op.base.x - (event.clientX - op.client[0]) / scale;
      view.y = op.base.y - (event.clientY - op.client[1]) / scale;
      applyView();
      return;
    }
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
    if (op.kind === "pan") {
      op = null;
      return;
    }
    const changed = op.kind !== "move" || op.bases.some(([t, b]) => !same(t.xywh, b));
    op = null;
    if (changed) emit();
  };
  svg.addEventListener("pointerup", finish);
  svg.addEventListener("pointercancel", finish);

  draw();
}
