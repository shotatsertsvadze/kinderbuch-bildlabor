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
    "Angaben": (
        "Angaben ergänzen",
        "Ergänzen Sie Verfasser, Ort, Jahr, Verlag, Rechte und Quelle des Buches.",
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


def area_counts(areas: list[dict]) -> tuple[int, int, int]:
    """Bestätigt, als Entwurf gespeichert, noch unberührt offen."""
    confirmed = sum(a["done"] for a in areas)
    drafts = sum(a["draft"] for a in areas)
    return confirmed, drafts, len(areas) - confirmed - drafts


def current_step(all_steps: list[tuple[str, bool]], pending: str | None) -> str:
    if pending is None:
        return f"alle {len(all_steps)} Schritte erledigt"
    number = [tab for tab, _ in all_steps].index(pending) + 1
    return f"Schritt {number} von {len(all_steps)} · {STEPS[pending][0]}"


def area_state(area: dict) -> str:
    if area["done"]:
        return "bestätigt"
    if area["draft"]:
        return "Entwurf gespeichert, Bestätigung offen"
    return f"offen ({review.status_label(area['status'])})"


def step_hint(tab: str, done: bool, areas: list[dict]) -> str:
    in_tab = [a for a in areas if a["tab_de"] == tab]
    count = (
        f" {sum(a['done'] for a in in_tab)} von {len(in_tab)} Prüfbereichen bestätigt."
        if in_tab
        else ""
    )
    return STEPS[tab][1] + count + (" Erledigt." if done else "")


def final_line(record: dict, blockers: int) -> str:
    if approved(record):
        return "**Endbestätigung:** erteilt (keine Ground-Truth-Freigabe)."
    if blockers:
        return (
            f"**Endbestätigung:** noch nicht erteilt; {blockers} offene fachliche "
            "Hinweise im Reiter „Prüfung“."
        )
    return "**Endbestätigung:** noch nicht erteilt."


def open_tab(key: str, tab: str) -> None:
    st.session_state[key] = tab


def render(record: dict, tabs_key: str, export_current: bool, blockers: int) -> None:
    pending = next_tab(record, export_current, blockers)
    all_steps = steps(record, export_current)
    areas = review.review_areas(record)
    confirmed, drafts, untouched = area_counts(areas)
    with st.container(key="review-guide", border=True):
        text, reviewer = st.columns([3, 2], vertical_alignment="bottom")
        with text:
            st.caption(f"PRÜFPFAD · {current_step(all_steps, pending).upper()}")
            st.markdown(
                f"**Nächste Handlung:** {ui.next_step(record, export_current, blockers)}"
            )
        with reviewer:
            ui.reviewer_input()
        st.progress(
            confirmed / len(areas),
            text=f"Prüfbereiche: {confirmed} von {len(areas)} bestätigt · "
            f"{drafts} als Entwurf gespeichert · {untouched} offen",
        )
        st.markdown(final_line(record, blockers))
        with st.expander(f"Prüfbereiche dieses Objekts ({len(areas)})"):
            st.markdown("\n".join(f"- {a['label_de']}: {area_state(a)}" for a in areas))
            st.caption(
                "Ein gespeicherter Entwurf ist noch keine Prüfung. Erst die Bestätigung mit "
                "Häkchen und Name zählt als bestätigter Bereich."
            )
        with st.container(horizontal=True, gap="xsmall"):
            for number, (tab, done) in enumerate(all_steps, start=1):
                st.button(
                    f"{number} · {STEPS[tab][0]}",
                    key=f"guide-{tab.lower()}",
                    help=step_hint(tab, done, areas),
                    type="primary" if tab == pending else "secondary",
                    icon=":material/check_circle:" if done else None,
                    on_click=open_tab,
                    args=(tabs_key, tab),
                )
    st.caption(
        "Die Schaltflächen des Prüfpfads führen zu den Arbeitsschritten; ein Schritt gilt erst "
        "als erledigt, wenn alle seine Prüfbereiche bestätigt sind. Die Reiter darunter zeigen "
        "alle Ansichten, auch bereits erledigte."
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
