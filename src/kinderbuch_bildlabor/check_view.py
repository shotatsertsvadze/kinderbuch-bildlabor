"""Reiter „Prüfung“ und „Export“ eines Objekts."""

import csv

import streamlit as st

from kinderbuch_bildlabor import actions, export, store, ui, validate
from kinderbuch_bildlabor.ui import Current

CATEGORY_STYLE = {
    validate.TECHNICAL: (st.error, ":material/error:",
                         "Formale Fehler in Daten oder Quelldateien. Sie verhindern eine verlässliche Nutzung."),
    validate.REVIEW: (st.warning, ":material/rule:",
                      "Offene fachliche Entscheidungen. Sie sind erwartbar und kein Datenfehler."),
    validate.NOT_RUN: (st.info, ":material/pending:",
                       "Bewusst nicht ausgeführt; über das Ergebnis ist nichts bekannt."),
}


def validation_tab(cur: Current, collection: list[dict]) -> None:
    findings = validate.run_all(cur.working, cur.src, collection)
    st.caption("Alle Prüfungen laufen gegen die gespeicherten Quelldateien, ohne Netzabruf. "
               "Doppelte Kennungen werden über die ganze Sammlung geprüft.")
    for category, label in validate.CATEGORY_LABELS_DE.items():
        show, icon, meaning = CATEGORY_STYLE[category]
        selected = [f for f in findings if f.category == category]
        st.markdown(f"#### {label}: {len(selected)}")
        st.caption(meaning)
        if selected:
            show("\n".join(f"- {f.message_de}" for f in selected), icon=icon)
        else:
            st.success("Keine.", icon=":material/check:")
    st.markdown("#### Bewusst leere optionale Angaben")
    st.write((", ".join(validate.unknown_optional_fields(cur.record)) or "Keine.") + " (kein Fehler)")
    with st.expander("Technische Codes der Befunde"):
        st.dataframe([{"Kategorie": f.category, "Code": f.code, "Meldung": f.message_de} for f in findings],
                     hide_index=True)


def export_state(cur: Current) -> tuple[str, list[dict] | None, dict | None]:
    """'none', 'current', 'stale' oder 'foreign' mit späteren Änderungen und Exportdaten."""
    json_path, _ = actions.export_paths(cur.id)
    if not json_path.exists():
        return "none", None, None
    exported = store.read_json(json_path)
    later = export.later_changes(cur.working, exported)
    state = "foreign" if later is None else "stale" if later else "current"
    return state, later, exported


def export_tab(cur: Current) -> None:
    json_path, csv_path = actions.export_paths(cur.id)
    st.write("Der JSON-Export enthält den vollständigen Arbeitsstand samt Herkunft, Rechten und Prüfprotokoll. "
             "Die CSV-Datei enthält eine Zeile je Region mit Herkunfts-, Rechte- und Prüfangaben.")
    state, later, exported = export_state(cur)
    st.button("JSON und CSV exportieren", key=f"{cur.id}-export", on_click=actions.run_export, args=(cur.id,),
              type="primary")
    if state == "none":
        st.info("Noch kein Export für dieses Objekt vorhanden.", icon=":material/info:")
    elif state == "foreign":
        st.error("Der vorhandene Export passt nicht zur Änderungsgeschichte dieses Arbeitsstands "
                 "(zum Beispiel nach einem Zurücksetzen der Arbeitskopie). Bitte neu exportieren.",
                 icon=":material/error:")
    elif state == "stale":
        changes = "\n".join(f"- {c['area_de']} ({ui.local_time(c['saved_at'])})" for c in later)
        st.warning(f"Export veraltet: erstellt {ui.local_time(exported['exported_at'])}. Danach gespeichert:\n"
                   f"{changes}\n\nDas sind spätere Bearbeitungen, keine Exportfehler. "
                   "Für die Rückladeprüfung bitte neu exportieren.", icon=":material/update:")
    else:
        st.success(f"Export aktuell: erstellt {ui.local_time(exported['exported_at'])}, seitdem nichts gespeichert.",
                   icon=":material/check:")

    if state != "none":
        roundtrip(cur, state, exported)
    if csv_path.exists():
        with st.expander(f"Inhalt der CSV-Datei (Stand des Exports)"):
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                st.dataframe(list(csv.DictReader(handle)), hide_index=True)
        st.caption(f"Dateien: {json_path.relative_to(store.DATA_DIR)}, {csv_path.relative_to(store.DATA_DIR)}")
    review_log(cur.record)


def roundtrip(cur: Current, state: str, exported: dict) -> None:
    st.markdown("#### Rückladeprüfung")
    st.button("Export erneut laden und prüfen", key=f"{cur.id}-roundtrip", on_click=actions.run_roundtrip,
              args=(cur.id,), disabled=state != "current")
    if state != "current":
        st.caption(":material/lock: Noch nicht möglich: Die Rückladeprüfung ist nur für einen aktuellen Export "
                   "aussagekräftig.")
        return
    result = st.session_state.get(f"{cur.id}-roundtrip-result")
    if not result or result[0] != exported["exported_at"]:
        return
    for label, ok in result[1]:
        if ok:
            st.success(f"Erhalten: {label}", icon=":material/check:")
        else:
            st.error(f"Abweichung: {label}", icon=":material/error:")
    if result[2]:
        st.markdown("Abweichende Felder im Export:\n" + "\n".join(f"- `{p}`" for p in result[2]))


def review_log(record: dict) -> None:
    st.markdown("#### Prüfprotokoll")
    log = record.get("review_log", [])
    if not log:
        st.info("Noch keine Änderungen oder Bestätigungen protokolliert.", icon=":material/info:")
        return
    st.dataframe([{"Zeitpunkt": ui.local_time(e["at"]), "Vorgang": e["action"], "Person": e.get("by", "–"),
                   "Bereich": e["area"]} for e in reversed(log)], hide_index=True)
    st.caption("Neueste Einträge zuerst. Einträge mit Person sind ausdrückliche Bestätigungen.")
