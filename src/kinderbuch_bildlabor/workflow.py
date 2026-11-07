"""Prüfpfad: nummerierte Schritte mit Stand und ein einheitliches „Weiter“ nach dem Speichern."""

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
        "Prüfen Sie Beschreibung und Suchbegriffe an den sichtbaren Motiven.",
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
        "Schreiben Sie JSON und CSV und prüfen Sie das zurückgelesene Ergebnis.",
    ),
}


def approved(record: dict) -> bool:
    return (
        bool(record.get("final_approval")) and record["status"] == review.FINAL_APPROVED
    )


def next_tab(
    record: dict, export_current: bool = False, blockers: int = 0
) -> str | None:
    """Reiter des nächsten offenen Schritts; None, wenn alles erledigt ist."""
    pending = next(
        (a["tab_de"] for a in review.review_areas(record) if not a["done"]), None
    )
    if pending:
        return pending
    if blockers or not approved(record):
        return "Prüfung"
    return None if export_current else "Export"


def steps(record: dict, export_current: bool) -> list[tuple[str, bool]]:
    """Schritte des Objekts mit Erledigt-Stand, in Arbeitsreihenfolge."""
    areas = review.review_areas(record)
    done = {
        tab: all(a["done"] for a in areas if a["tab_de"] == tab)
        for tab in dict.fromkeys(a["tab_de"] for a in areas)
    }
    # Ein aktueller Export eines ungeprüften Entwurfs ist noch kein erledigter Schritt
    return [
        *done.items(),
        ("Prüfung", approved(record)),
        ("Export", export_current and approved(record)),
    ]


def open_tab(key: str, tab: str) -> None:
    st.session_state[key] = tab


def render(record: dict, tabs_key: str, export_current: bool, blockers: int) -> None:
    pending = next_tab(record, export_current, blockers)
    all_steps = steps(record, export_current)
    with st.container(key="review-guide", border=True):
        text, reviewer = st.columns([3, 2], vertical_alignment="bottom")
        with text:
            st.caption(
                f"PRÜFPFAD · {sum(d for _, d in all_steps)} VON {len(all_steps)} SCHRITTEN ERLEDIGT"
            )
            st.markdown(
                f"**Nächster Schritt:** {ui.next_step(record, export_current, blockers)}"
            )
        with reviewer:
            ui.reviewer_input()
        with st.container(horizontal=True, gap="xsmall"):
            for number, (tab, done) in enumerate(all_steps, start=1):
                label, hint = STEPS[tab]
                st.button(
                    f"{number} · {label}",
                    key=f"guide-{tab.lower()}",
                    help=f"{hint} Erledigt." if done else hint,
                    type="primary" if tab == pending else "secondary",
                    icon=":material/check_circle:" if done else None,
                    on_click=open_tab,
                    args=(tabs_key, tab),
                )
    st.caption(
        "Der Prüfpfad führt Schritt für Schritt. Die Reiter darunter zeigen alle Ansichten, "
        "auch bereits erledigte."
    )


def continue_button(object_id: str, record: dict, key: str) -> None:
    """Primäre „Weiter“-Schaltfläche zum nächsten offenen Schritt, direkt nach dem Speichern."""
    target = next_tab(record)
    if target is None:
        return
    st.button(
        f"Weiter: {STEPS[target][0]}",
        key=key,
        type="primary",
        icon=":material/arrow_forward:",
        help=STEPS[target][1],
        on_click=open_tab,
        args=(f"{object_id}-tabs", target),
    )
