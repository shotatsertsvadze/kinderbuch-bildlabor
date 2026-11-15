"""Tastenkürzel der Prüfung: setzen nur den Reiter bzw. den Fokus, bestätigen nie etwas."""

import streamlit as st

from kinderbuch_bildlabor import store, workflow

KEYS = {"n"}
HELP = (
    "Tasten außerhalb von Eingabefeldern: n = nächster offener Schritt, "
    "b = Bestätigung in der aktuellen Ansicht fokussieren (bestätigt wird erst mit Leertaste und Name), "
    "? = diese Hilfe vorlesen."
)
# Ohne „b“: In der öffentlichen Ansicht gibt es nichts zu bestätigen
DEMO_HELP = (
    "Tasten außerhalb von Eingabefeldern: n = nächster offener Schritt, "
    "? = diese Hilfe vorlesen."
)
JS = """
export default function (component) {
  const { data, parentElement, setStateValue } = component;
  parentElement.replaceChildren();
  const box = document.createElement("details");
  box.style.cssText = "font-size:0.8125rem;color:var(--bl-ink-muted, #555B62)";
  const summary = document.createElement("summary");
  summary.textContent = "Tastenkürzel";
  summary.style.cssText = "cursor:pointer;min-height:1.75rem";
  const help = document.createElement("p");
  help.tabIndex = -1;
  help.style.cssText = "margin:0.25rem 0 0;font:inherit;line-height:1.5";
  help.textContent = data.help;
  box.append(summary, help);
  parentElement.append(box);
  const typing = (t) => t instanceof Element && (t.closest("input,textarea,select,svg,[contenteditable]") !== null);
  const onKey = (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey || typing(event.target)) return;
    if (event.key === "n") {
      setStateValue("press", { seq: `${Date.now()}-${Math.random()}`, key: "n" });
    } else if (event.key === "b") {
      const panel = document.querySelector('[role="tabpanel"]:not([hidden])') ?? document;
      const boxes = [...panel.querySelectorAll('input[type="checkbox"]')];
      (boxes.find((b) => !b.checked) ?? boxes[0])?.focus();
    } else if (event.key === "?") {
      box.open = true;
      help.focus();
    }
  };
  document.addEventListener("keydown", onKey);
  return () => document.removeEventListener("keydown", onKey);
}
"""
COMPONENT = st.components.v2.component(
    "bildlabor_review_keys", html="<div></div>", js=JS
)


def normalize_press(state) -> dict | None:
    """Prüft das Tastenereignis auf dem Server; unbekannte Tasten werden verworfen."""
    press = state.get("press") if isinstance(state, dict) else None
    if (
        not isinstance(press, dict)
        or not isinstance(press.get("seq"), str)
        or press.get("key") not in KEYS
    ):
        return None
    return press


def handle(
    state, last_seq, record: dict, tabs_key: str, export_current: bool, blockers: int
) -> str | None:
    """Öffnet bei neuem Ereignis „n“ den nächsten offenen Reiter; gibt dessen seq zurück."""
    press = normalize_press(state)
    if press is None or press["seq"] == last_seq:
        return last_seq
    if tab := workflow.next_tab(record, export_current, blockers):
        workflow.open_tab(tabs_key, tab)
    return press["seq"]


def render(record: dict, tabs_key: str, export_current: bool, blockers: int) -> None:
    instance = f"{tabs_key}-keys"
    seq_key = f"{instance}-seq"

    def on_press() -> None:
        st.session_state[seq_key] = handle(
            st.session_state.get(instance),
            st.session_state.get(seq_key),
            record,
            tabs_key,
            export_current,
            blockers,
        )

    COMPONENT(
        key=instance,
        data={"help": DEMO_HELP if store.DEMO else HELP},
        default={"press": None},
        on_press_change=on_press,
    )
