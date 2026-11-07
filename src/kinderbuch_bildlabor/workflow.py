"""Kurzer Prüfpfad mit direktem Sprung in den passenden Reiter."""

import streamlit as st

from kinderbuch_bildlabor import review, ui

STEPS = {
    "Regionen": (
        "Bild prüfen",
        "Prüfen Sie, ob der Rahmen die Illustration vollständig erfasst.",
    ),
    "Klassifikation": (
        "Klassen vergleichen",
        "Vergleichen Sie beide Colibri-Klassen mit dem Bild und begründen Sie Ihre Wahl.",
    ),
    "Beschreibung": (
        "Bild beschreiben",
        "Prüfen Sie die Beschreibung und die Suchbegriffe anhand der sichtbaren Motive.",
    ),
    "Transkription": (
        "Text abgleichen",
        "Vergleichen Sie die Transkription mit dem Bildausschnitt.",
    ),
    "Prüfung": (
        "Prüfung abschließen",
        "Entscheiden Sie offene Hinweise und erteilen Sie die Endbestätigung.",
    ),
    "Export": (
        "Ergebnis exportieren",
        "Speichern Sie JSON und CSV und prüfen Sie das zurückgelesene Ergebnis.",
    ),
}


def open_tab(key: str, tab: str) -> None:
    st.session_state[key] = tab


def render(record: dict, tabs_key: str, export_current: bool, blockers: int) -> None:
    areas = review.review_areas(record)
    area_tabs = list(dict.fromkeys(area["tab_de"] for area in areas))
    pending = next((area["tab_de"] for area in areas if not area["done"]), None)
    approved = (
        record.get("final_approval") and record["status"] == review.FINAL_APPROVED
    )
    if pending is None:
        if blockers or not approved:
            pending = "Prüfung"
        elif not export_current:
            pending = "Export"

    with st.container(key="review-guide", border=True):
        st.markdown("**Ihr Prüfpfad**")
        st.markdown(
            f"**Nächster Schritt** · {ui.next_step(record, export_current, blockers)}"
        )
        if not st.session_state.get("reviewer", "").strip():
            st.caption("Tragen Sie zum Speichern Ihren Namen in der Seitenleiste ein.")
        done = sum(area["done"] for area in areas)
        st.progress(
            done / len(areas), text=f"{done} von {len(areas)} Prüfbereichen bestätigt"
        )
        with st.container(horizontal=True, gap="xsmall"):
            for number, tab in enumerate([*area_tabs, "Prüfung", "Export"], start=1):
                label, hint = STEPS[tab]
                st.button(
                    f"{number:02d} · {label}",
                    key=f"guide-{tab.lower()}",
                    help=hint,
                    type="primary" if tab == pending else "secondary",
                    on_click=open_tab,
                    args=(tabs_key, tab),
                )
