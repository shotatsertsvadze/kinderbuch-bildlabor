"""Reiter „Prüfung“ und „Export“ eines Objekts."""

import streamlit as st

from kinderbuch_bildlabor import (
    actions,
    decision_view,
    review,
    ui,
    validate,
    workflow,
)
from kinderbuch_bildlabor.ui import Current

CATEGORY_STYLE = {
    validate.TECHNICAL: (
        st.error,
        ui.ERROR,
        "Formale Fehler in Daten oder Quelldateien. Sie verhindern eine verlässliche Nutzung.",
    ),
    validate.REVIEW: (
        st.warning,
        ":material/rule:",
        "Offene fachliche Entscheidungen. Sie sind erwartbar und kein Datenfehler.",
    ),
    validate.NOT_RUN: (
        st.info,
        ui.PENDING,
        "Bewusst nicht ausgeführt; über das Ergebnis ist nichts bekannt.",
    ),
    validate.DOCUMENTED: (
        st.success,
        ui.CONFIRMED,
        "Belegte Unterschiede, zu denen eine benannte Person eine Entscheidung mit Begründung "
        "festgehalten hat. Sie bleiben sichtbar und sperren die Endbestätigung nicht.",
    ),
}


def validation_tab(cur: Current, collection: list[dict]) -> None:
    findings = validate.run_all(cur.working, cur.src, collection)
    state = review.readiness(cur.record, findings)
    ui.section("Stand des Objekts")
    st.write(state)
    if workflow.approved(cur.record):
        workflow.continue_button(cur.id, cur.record, f"{cur.id}-final-continue")
    decisions(cur, findings)
    final_approval(cur, state, findings)
    ui.section("Alle Prüfergebnisse")
    st.caption(
        "Alle Prüfungen laufen gegen die gespeicherten Quelldateien, ohne Netzabruf. "
        "Doppelte Kennungen werden über die ganze Sammlung geprüft."
    )
    for category, label in validate.CATEGORY_LABELS_DE.items():
        show, icon, meaning = CATEGORY_STYLE[category]
        selected = [f for f in findings if f.category == category]
        ui.subsection(f"{label}: {len(selected)}")
        st.caption(meaning)
        if selected:
            show("\n".join(f"- {f.message_de}" for f in selected), icon=icon)
        else:
            st.success("Keine.", icon=ui.OK)
    ui.subsection("Bewusst leere optionale Angaben")
    st.write(
        (", ".join(validate.unknown_optional_fields(cur.record)) or "Keine.")
        + " (kein Fehler)"
    )
    with st.expander("Technische Codes der Befunde"):
        st.dataframe(
            [
                {"Kategorie": f.category, "Code": f.code, "Meldung": f.message_de}
                for f in findings
            ],
            hide_index=True,
        )


def final_approval(cur: Current, state: str, findings: list) -> None:
    ui.section("Endbestätigung des Objekts")
    st.caption(
        "Eine benannte Person hat den gesamten gespeicherten Arbeitsstand durchgesehen. Das ist "
        "keine Ground-Truth-Freigabe; dafür fehlt eine unabhängige Zweitprüfung. Jede spätere "
        "Inhaltsänderung hebt sie auf."
    )
    blockers = validate.approval_blockers(findings)
    if blockers:
        st.warning(
            "Endbestätigung gesperrt:\n"
            + "\n".join(f"- {f.message_de}" for f in blockers)
        )
    approval = cur.record.get("final_approval")
    if approval:
        st.success(
            f"Endbestätigung erteilt von {approval['by']} · {ui.local_time(approval['at'])}"
        )
        workflow.continue_button(cur.id, cur.record, f"{cur.id}-approved-continue")
        return
    ack = st.checkbox(
        "Ich bestätige den gesamten gespeicherten Arbeitsstand; keine Ground-Truth-Freigabe.",
        key=f"{cur.id}-final-ack",
    )
    reason = (
        "Erst alle Prüfbereiche bestätigen und die gesperrten Punkte oben klären."
        if state != "Bereit zur Endbestätigung"
        else "Tragen Sie oben im Prüfpfad unter „Prüfende Person“ Ihren Namen ein."
        if not actions.reviewer()
        else "Bitte zuerst das Häkchen setzen."
        if not ack
        else None
    )
    st.button(
        "Endbestätigung erteilen",
        key=f"{cur.id}-final-confirm",
        disabled=reason is not None,
        type="primary",
        icon=ui.CONFIRMED,
        on_click=actions.approve_object,
        args=(cur.id, cur.record, ack),
    )
    if reason:
        st.caption(f"{ui.LOCK} Noch nicht möglich: {reason}")


def decisions(cur: Current, findings: list) -> None:
    decidable = [f for f in findings if validate.decidable(cur.record, f)]
    if not decidable:
        return
    ui.section("Hinweise begründet entscheiden")
    st.caption(
        "Belegte Unterschiede lassen sich nicht wegklicken. Halten Sie mit Ihrem Namen fest, wie "
        "damit umgegangen wird, und begründen Sie das. „Nicht entscheidbar“ lässt den Hinweis offen."
    )
    for finding in decidable:
        with st.container(border=True):
            ui.source_text(finding.message_de)
            if finding.code == review.CLASSIFICATION:
                entry = review.decision(cur.record, finding.code, finding.message_de)
                st.caption(
                    (f"{entry['outcome_de']} ({entry['by']}). " if entry else "Offen. ")
                    + "Entschieden wird im Reiter „Klassifikation“ am Bild."
                )
            else:
                decision_view.decision_form(cur, finding.code, finding.message_de)
