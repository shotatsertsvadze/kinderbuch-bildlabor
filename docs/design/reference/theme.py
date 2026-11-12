"""Gestaltungs-Token für eigenes CSS (workflow.css) und Seitensprache.

Referenzumsetzung zu docs/design/DESIGN_SYSTEM.md. Ziel: src/kinderbuch_bildlabor/theme.py.
Streamlits eigene Farben stehen in .streamlit/config.toml; diese Werte hier sind dieselben Token
für Flächen, die nur unser CSS gestaltet (Passepartout, Karten, Eingaberänder). Beide Dateien
gemeinsam ändern.
"""

import streamlit as st

TOKENS: dict[str, dict[str, str]] = {
    "light": {
        "surface": "#FFFDF9",
        "sunken": "#ECE5D7",
        "border": "#DED4C3",
        "border-strong": "#C4B79F",
        "control": "#8C8170",
        "ink": "#1D2130",
        "ink-muted": "#5A5446",
        "primary": "#1F4E79",
        "ok": "#2B6639",
        "mat": "#E3E2DF",
        "shadow-1": "0 1px 2px rgba(29, 33, 48, 0.06)",
        "shadow-scan": "0 1px 2px rgba(40, 30, 15, 0.20), 0 6px 18px rgba(40, 30, 15, 0.14)",
    },
    "dark": {
        "surface": "#24231F",
        "sunken": "#2E2C27",
        "border": "#3D3A33",
        "border-strong": "#57534A",
        "control": "#857D6E",
        "ink": "#ECE6DA",
        "ink-muted": "#B4AC9C",
        "primary": "#8DB4E2",
        "ok": "#9FD3A8",
        "mat": "#121211",
        "shadow-1": "0 1px 2px rgba(0, 0, 0, 0.4)",
        "shadow-scan": "0 1px 2px rgba(0, 0, 0, 0.5), 0 6px 18px rgba(0, 0, 0, 0.45)",
    },
}


def mode() -> str:
    """Aktiver Modus; ohne Browserangabe (z. B. in AppTest) gilt Hell."""
    return "dark" if st.context.theme.type == "dark" else "light"


def inject() -> None:
    """Setzt die CSS-Variablen --bl-* für den aktiven Modus und die Seitensprache Deutsch.

    lang="de" lässt Screenreader deutsch vorlesen und aktiviert die Silbentrennung (hyphens: auto).
    """
    variables = " ".join(
        f"--bl-{name}: {value};" for name, value in TOKENS[mode()].items()
    )
    st.html(f"<style>:root {{ {variables} }}</style>")
    st.html(
        "<script>document.documentElement.lang = 'de';</script>",
        unsafe_allow_javascript=True,
    )
