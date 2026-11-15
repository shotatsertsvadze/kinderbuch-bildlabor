"""Gestaltungs-Token für eigenes CSS (workflow.css) und Seitensprache.

Umsetzung von docs/design/DESIGN_SYSTEM.md.
Streamlits eigene Farben stehen in .streamlit/config.toml; diese Werte hier sind dieselben Token
für Flächen, die nur unser CSS gestaltet (Passepartout, Karten, Prüfpfad-Leiste, Eingaberänder).
Beide Dateien gemeinsam ändern.
"""

import streamlit as st

TOKENS: dict[str, dict[str, str]] = {
    "light": {
        "canvas": "#F4F5F3",
        "surface": "#FFFFFF",
        "sunken": "#EBEDEA",
        "border": "#DCDFDA",
        "border-strong": "#C3C8C1",
        "control": "#878D86",
        "ink": "#15181C",
        "ink-muted": "#555B62",
        "primary": "#2448C9",
        "primary-tint": "#E9EDFB",
        "on-primary": "#FFFFFF",
        "ok": "#146C3A",
        "draft": "#A26300",
        "open": "#C9CDC7",
        "mat": "#E2E3E1",
        "shadow-1": "0 1px 2px rgba(21, 24, 28, 0.05), 0 1px 1px rgba(21, 24, 28, 0.03)",
        "shadow-scan": "0 1px 2px rgba(0, 0, 0, 0.16), 0 8px 24px rgba(0, 0, 0, 0.12)",
    },
    "dark": {
        "canvas": "#111315",
        "surface": "#1A1D20",
        "sunken": "#23272B",
        "border": "#30353A",
        "border-strong": "#454B52",
        "control": "#7C838B",
        "ink": "#E8EBED",
        "ink-muted": "#A2A9B1",
        "primary": "#94AAFF",
        "primary-tint": "#1D2547",
        "on-primary": "#0B1640",
        "ok": "#86D6A2",
        "draft": "#F5C26B",
        "open": "#3A4047",
        "mat": "#0B0C0D",
        "shadow-1": "0 1px 2px rgba(0, 0, 0, 0.4)",
        "shadow-scan": "0 1px 2px rgba(0, 0, 0, 0.5), 0 8px 24px rgba(0, 0, 0, 0.45)",
    },
}


# Hell oder dunkel nach der Helligkeit des tatsächlich gezeigten Hintergrunds
THEME_SCRIPT = """
window.__blSyncTheme = () => {
  const app = document.querySelector('.stApp') || document.body;
  const [r, g, b] = getComputedStyle(app).backgroundColor.match(/\\d+/g).map(Number);
  document.documentElement.dataset.blTheme = 0.2126 * r + 0.7152 * g + 0.0722 * b < 128 ? 'dark' : 'light';
};
if (!window.__blThemeWatch) {
  window.__blThemeWatch = true;
  let queued = false;
  // Nach einem Themenwechsel ändern sich die Klassen der Streamlit-Elemente; zweiter Blick nach
  // einem möglichen Farbübergang
  const later = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; window.__blSyncTheme(); });
    setTimeout(window.__blSyncTheme, 400);
  };
  new MutationObserver(later).observe(document.body, { attributes: true, attributeFilter: ['class'], subtree: true });
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', later);
}
window.__blSyncTheme();
"""

# st.subheader hat keine Ebenenwahl und erzeugt h3 unter dem h1-Titel; aria-level ordnet die
# Abschnitte als Ebene 2 ein, ohne die Darstellung zu ändern.
PAGE_SCRIPT = """
document.documentElement.lang = 'de';
if (!window.__blHeadingLevels) {
  window.__blHeadingLevels = true;
  const fix = () => document
    .querySelectorAll('[data-testid="stMain"] [data-testid="stHeading"] h3')
    .forEach((h) => h.setAttribute('aria-level', '2'));
  new MutationObserver(fix).observe(document.body, { childList: true, subtree: true });
  fix();
}
"""


def variables(mode: str) -> str:
    return " ".join(f"--bl-{name}: {value};" for name, value in TOKENS[mode].items())


def inject() -> None:
    """Setzt die CSS-Variablen --bl-* für Hell und Dunkel und die Seitensprache Deutsch.

    Welcher Satz gilt, entscheidet THEME_SCRIPT im Browser nach dem tatsächlich gezeigten Thema:
    Streamlit wechselt das Thema sofort, ein serverseitig gewählter Satz bliebe bis zum nächsten
    Lauf stehen (dunkle Schrift auf dunklem Kobalt, 2,4:1).
    lang="de" lässt Screenreader deutsch vorlesen und aktiviert die Silbentrennung (hyphens: auto).
    """
    st.html(
        f"<style>:root {{ {variables('light')} }} "
        f':root[data-bl-theme="dark"] {{ {variables("dark")} }}</style>'
    )
    st.html(
        f"<script>{PAGE_SCRIPT}{THEME_SCRIPT}</script>", unsafe_allow_javascript=True
    )
