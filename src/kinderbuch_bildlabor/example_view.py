"""Startseite: das mitgelieferte, persönlich geprüfte Beispiel (unveränderter Export)."""

import streamlit as st

from kinderbuch_bildlabor import store, ui

EXAMPLE_DIR = store.ROOT / "docs" / "ergebnis"
EXAMPLE = "genovefa-scan-022"


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
                data=(EXAMPLE_DIR / name).read_bytes(),
                file_name=name if name != "README.md" else "ergebnis-erlaeuterung.md",
                mime=mime,
                key=f"example-{name}",
                icon=":material/download:",
                on_click="ignore",
            )
