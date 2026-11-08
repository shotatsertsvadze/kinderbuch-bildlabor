"""Startseite: das mitgelieferte, persönlich geprüfte Beispiel (unveränderter Export)."""

import re

import streamlit as st

from kinderbuch_bildlabor import store, ui

EXAMPLE_DIR = store.ROOT / "docs" / "ergebnis"
EXAMPLE = "genovefa-scan-022"
# Markdown-Bild oder -Link mit relativem Ziel; externe Adressen bleiben unberührt
RELATIVE_LINK = re.compile(r"(!?)\[([^\]]*)\]\((?![a-z]+://)([^)\s]+)\)")
DOWNLOAD_NOTE = (
    "> Erläuterung zum geprüften Beispiel aus dem Projekt Kinderbuch-Bildlabor "
    "(im Projekt: docs/ergebnis/README.md). Für diesen Download sind Verweise auf "
    "Projektdateien als Text angegeben. JSON und CSV gibt es auf der Startseite der "
    "Anwendung einzeln zum Herunterladen; Abbildung und weitere Dokumente liegen im "
    "Projektordner.\n\n"
)


def render() -> None:
    exported = store.read_json(EXAMPLE_DIR / f"{EXAMPLE}.json")
    record = exported["record"]
    with st.container(key="finished-example", border=True):
        ui.section("Abgeschlossenes Beispiel: Genovefa, Scan 22")
        st.caption(
            "Unveränderter Export einer Prüfung durch die bewerbende Person, mitgeliefert unter "
            "docs/ergebnis/. Unabhängig davon startet die Anwendung mit dem Quellstand; die "
            "Fallstudie darunter zeigt den Stand Ihres eigenen Datenordners."
        )
        st.markdown("\n".join(decision_lines(record)))
        approval = record.get("final_approval")
        if approval:
            st.markdown(
                f"Endbestätigung: {approval['by']}, {ui.local_time(approval['at'])}. "
                "Keine Ground-Truth-Freigabe, keine Zweitprüfung."
            )
        st.caption(
            "Begründungen und Name stehen wörtlich wie gespeichert. Einschränkungen nennt die "
            "Erläuterung."
        )
        downloads()


def decision_lines(record: dict) -> list[str]:
    return [
        f"- **{entry['outcome_de']}** · Begründung: „{entry['rationale_de']}“ · "
        f"{entry['by']}, {ui.local_time(entry['at'])}"
        for entry in record.get("decisions", {}).values()
    ]


def standalone_explanation() -> bytes:
    """Erläuterung ohne relative Verweise, weil sie außerhalb des Projektordners gelesen wird."""
    text = (EXAMPLE_DIR / "README.md").read_text(encoding="utf-8")

    def as_text(match: re.Match) -> str:
        image, label, target = match.groups()
        if image:
            return f"(Abbildung im Projektordner unter docs/ergebnis/{target}: {label})"
        return label

    return (DOWNLOAD_NOTE + RELATIVE_LINK.sub(as_text, text)).encode("utf-8")


def downloads() -> None:
    files = [
        (f"{EXAMPLE}.json", "JSON herunterladen", "application/json"),
        (f"{EXAMPLE}.csv", "CSV herunterladen", "text/csv"),
        ("README.md", "Erläuterung herunterladen", "text/markdown"),
    ]
    with st.container(horizontal=True):
        for name, label, mime in files:
            st.download_button(
                label,
                data=standalone_explanation()
                if name == "README.md"
                else (EXAMPLE_DIR / name).read_bytes(),
                file_name=name if name != "README.md" else "ergebnis-erlaeuterung.md",
                mime=mime,
                key=f"example-{name}",
                icon=":material/download:",
                on_click="ignore",
            )
