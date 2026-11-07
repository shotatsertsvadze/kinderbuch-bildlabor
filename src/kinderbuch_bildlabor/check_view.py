"""Reiter „Prüfung“ und „Export“ eines Objekts."""

import csv
import json

import streamlit as st

from kinderbuch_bildlabor import (
    actions,
    decision_view,
    export,
    review,
    store,
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


def export_state(cur: Current) -> tuple[str, list[dict] | None, dict | None]:
    """'none', 'damaged', 'current', 'stale' oder 'foreign' mit späteren Änderungen und Exportdaten."""
    json_path, _ = actions.export_paths(cur.id)
    if not json_path.exists():
        return "none", None, None
    try:
        exported = store.read_json(json_path)
    except json.JSONDecodeError:
        return "damaged", None, None
    later = export.later_changes(cur.working, exported)
    state = "foreign" if later is None else "stale" if later else "current"
    return state, later, exported


def export_tab(cur: Current) -> None:
    json_path, csv_path = actions.export_paths(cur.id)
    st.write(
        "Der JSON-Export enthält den vollständigen Arbeitsstand samt Herkunft, Rechten und Prüfprotokoll. "
        "Die CSV-Datei enthält eine Zeile je Region mit Herkunfts-, Rechte- und Prüfangaben."
    )
    state, later, exported = export_state(cur)
    st.button(
        "JSON und CSV exportieren",
        key=f"{cur.id}-export",
        on_click=actions.run_export,
        args=(cur.id,),
        type="secondary" if state == "current" else "primary",
        icon=":material/download:",
    )
    if state == "none":
        st.info("Noch kein Export für dieses Objekt vorhanden.", icon=ui.INFO)
    elif state == "damaged":
        st.error(
            "Die vorhandene Exportdatei ist beschädigt und kann nicht gelesen werden. "
            "Ein neuer Export ersetzt sie.",
            icon=ui.ERROR,
        )
    elif state == "foreign":
        st.error(
            "Der vorhandene Export passt nicht zur Änderungsgeschichte dieses Arbeitsstands "
            "(zum Beispiel nach einem Zurücksetzen der Arbeitskopie). Bitte neu exportieren.",
            icon=ui.ERROR,
        )
    elif state == "stale":
        assert later is not None and exported is not None
        changes = "\n".join(
            f"- {c['area_de']} ({ui.local_time(c['saved_at'])})" for c in later
        )
        st.warning(
            f"Export veraltet: erstellt {ui.local_time(exported['exported_at'])}. Danach gespeichert:\n"
            f"{changes}\n\nDas sind spätere Bearbeitungen, keine Exportfehler. "
            "Für die Rückladeprüfung bitte neu exportieren.",
            icon=":material/update:",
        )
    else:
        assert exported is not None
        st.success(
            f"Export aktuell: erstellt {ui.local_time(exported['exported_at'])}, seitdem nichts gespeichert.",
            icon=ui.OK,
        )

    if state not in ("none", "damaged"):
        assert exported is not None
        roundtrip(cur, state, exported)
    if csv_path.exists():
        with st.expander("Inhalt der CSV-Datei (Stand des Exports)"):
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                st.dataframe(list(csv.DictReader(handle)), hide_index=True)
        st.caption(
            f"Dateien: {json_path.relative_to(store.DATA_DIR)}, {csv_path.relative_to(store.DATA_DIR)}"
        )
    review_log(cur.record)


def roundtrip(cur: Current, state: str, exported: dict) -> None:
    ui.section("Rückladeprüfung")
    st.button(
        "Export erneut laden und prüfen",
        key=f"{cur.id}-roundtrip",
        on_click=actions.run_roundtrip,
        args=(cur.id,),
        disabled=state != "current",
        type="primary",
    )
    if state != "current":
        st.caption(
            f"{ui.LOCK} Noch nicht möglich: Die Rückladeprüfung ist nur für einen aktuellen Export "
            "aussagekräftig."
        )
        return
    result = st.session_state.get(f"{cur.id}-roundtrip-result")
    if not result or result[0] != exported["exported_at"]:
        return
    if all(ok for _, ok in result[1]) and not result[2]:
        if not workflow.approved(cur.record):
            st.info(
                "Export vollständig zurückgelesen. Das Objekt ist noch nicht endbestätigt; "
                "dieser Export ist ein Zwischenstand.",
                icon=ui.INFO,
            )
            workflow.continue_button(cur.id, cur.record, f"{cur.id}-export-continue")
        else:
            st.success(
                "Fertig: Endbestätigt, exportiert und vollständig zurückgelesen.",
                icon=ui.CONFIRMED,
            )
            st.button(
                "Weiter: zurück zur Sammlung",
                key=f"{cur.id}-export-continue",
                type="primary",
                icon=":material/arrow_forward:",
                on_click=actions.open_object,
                args=("sammlung",),
            )
    for label, ok in result[1]:
        if ok:
            st.success(f"Erhalten: {label}", icon=ui.OK)
        else:
            st.error(f"Abweichung: {label}", icon=ui.ERROR)
    if result[2]:
        st.markdown(
            "Abweichende Felder im Export:\n" + "\n".join(f"- `{p}`" for p in result[2])
        )


def review_log(record: dict) -> None:
    ui.section("Prüfprotokoll")
    log = record.get("review_log", [])
    if not log:
        st.info(
            "Noch keine Änderungen oder Bestätigungen protokolliert.",
            icon=ui.INFO,
        )
        return
    st.dataframe(
        [
            {
                "Zeitpunkt": ui.local_time(e["at"]),
                "Vorgang": e["action"],
                "Person": e.get("by", "–"),
                "Bereich": e["area"],
            }
            for e in reversed(log)
        ],
        hide_index=True,
    )
    st.caption(
        "Neueste Einträge zuerst. Einträge mit Person sind ausdrückliche Bestätigungen."
    )
