"""Reiter „Export“: Dateien speichern, erneut laden und prüfen, mit sichtbarem Stand."""

import csv
import json
from pathlib import Path

import streamlit as st

from kinderbuch_bildlabor import actions, export, store, ui, workflow
from kinderbuch_bildlabor.ui import Current

ICONS = {
    "done": ":material/check_circle:",
    "open": ":material/radio_button_unchecked:",
    "warn": ":material/warning:",
    "error": ":material/error:",
}


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


def verification(cur: Current, state: str, exported: dict | None) -> dict | None:
    """Prüfergebnis dieser Sitzung, nur wenn es genau zur gespeicherten JSON-Datei gehört."""
    result = st.session_state.get(actions.roundtrip_key(cur.id))
    if state != "current" or not result or exported is None:
        return None
    json_path, _ = actions.export_paths(cur.id)
    if result["exported_at"] != exported["exported_at"] or result[
        "digest"
    ] != actions.file_digest(json_path):
        return None
    return result


def passed(result: dict) -> bool:
    return all(ok for _, ok in result["report"]) and not result["differing"]


def export_tab(cur: Current) -> None:
    json_path, csv_path = actions.export_paths(cur.id)
    state, later, exported = export_state(cur)
    result = verification(cur, state, exported)
    approved = workflow.approved(cur.record)
    stages(state, exported, result, approved)
    save_section(cur, state, later, exported, result, approved, json_path, csv_path)
    verify_section(cur, state, result, approved)
    if csv_path.exists():
        with st.expander("Inhalt der CSV-Datei (Stand des Exports)"):
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                st.dataframe(list(csv.DictReader(handle)), hide_index=True)
    review_log(cur.record)


def stages(state: str, exported: dict | None, result: dict | None, approved: bool):
    st.caption("Export vorbereiten → Dateien speichern → Export prüfen")
    prepare = (
        ("done", "Arbeitsstand endbestätigt")
        if approved
        else ("warn", "Arbeitsstand ist ein Entwurf, nicht endbestätigt")
    )
    save = {
        "none": ("open", "Noch kein Export"),
        "damaged": ("error", "Exportdatei beschädigt"),
        "foreign": ("error", "Export passt nicht zum Arbeitsstand"),
        "stale": ("warn", "Veraltet: danach gespeichert"),
    }.get(state) or ("done", f"Gespeichert {ui.local_time(exported['exported_at'])}")  # type: ignore[index]
    if state != "current":
        check = ("open", "Erst einen aktuellen Export speichern")
    elif result is None:
        check = ("open", "Noch nicht geprüft")
    elif passed(result):
        check = ("done", f"Geprüft {ui.local_time(result['checked_at'])}")
    else:
        check = ("error", "Prüfung fehlgeschlagen")
    with st.container(horizontal=True, key="export-stages"):
        for number, (title, (kind, text)) in enumerate(
            zip(
                ["Export vorbereiten", "Dateien speichern", "Export prüfen"],
                [prepare, save, check],
            ),
            start=1,
        ):
            with st.container(border=True):
                st.markdown(f"**{number} · {title}**  \n{ICONS[kind]} {text}")


def save_section(cur, state, later, exported, result, approved, json_path, csv_path):
    ui.section("Dateien speichern")
    st.caption(
        "Speichert den aktuellen Arbeitsstand als JSON- und CSV-Datei im Exportordner."
    )
    if st.button(
        "JSON und CSV exportieren",
        key=f"{cur.id}-export",
        type="secondary" if state == "current" else "primary",
        icon=":material/download:",
    ):
        with st.spinner("JSON und CSV werden gespeichert …"):
            actions.run_export(cur.id)
        st.rerun()
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
        changes = "\n".join(
            f"- {c['area_de']} ({ui.local_time(c['saved_at'])})" for c in later
        )
        st.warning(
            f"Export veraltet: erstellt {ui.local_time(exported['exported_at'])}. Danach gespeichert:\n"
            f"{changes}\n\nDas sind spätere Bearbeitungen, keine Exportfehler. Eine frühere "
            "Prüfung gilt für den geänderten Stand nicht mehr. Nächster Schritt: neu exportieren.",
            icon=":material/update:",
        )
    else:
        saved_panel(cur, exported, result, approved, json_path, csv_path)


def saved_panel(cur, exported, result, approved, json_path: Path, csv_path: Path):
    with st.container(border=True, key=f"{cur.id}-saved-panel"):
        st.success(
            "JSON und CSV gespeichert. Export aktuell: erstellt "
            f"{ui.local_time_exact(exported['exported_at'])}, seitdem nichts gespeichert.",
            icon=ui.OK,
        )
        st.markdown(
            f"Dateien: `{json_path.name}` und `{csv_path.name}`  \nOrdner: `{json_path.parent}`"
        )
        if not approved:
            st.caption(
                ":material/edit_note: Zwischenstand: Das Objekt ist nicht endbestätigt. Der Export "
                "dokumentiert den Entwurf und ist keine Freigabe."
            )
        replaced = st.session_state.get(f"{cur.id}-export-replaced")
        if replaced and replaced[0] == exported["exported_at"] and replaced[1]:
            st.info(
                f"Dieser Export ersetzt den vom {ui.local_time_exact(replaced[1])}. Dessen "
                "Prüfung galt nur der alten Datei und gilt für die neue nicht.",
                icon=":material/restart_alt:",
            )
        downloads(cur, exported, json_path, csv_path)
        if result is None:
            st.markdown(
                "**Nächster Schritt:** Gespeicherten Export erneut laden und prüfen."
            )


def downloads(cur, exported, json_path: Path, csv_path: Path):
    """Liefert genau die gespeicherten Dateien, keine neu erzeugte Fassung."""
    with st.container(horizontal=True):
        st.download_button(
            "JSON herunterladen",
            data=json_path.read_bytes(),
            file_name=json_path.name,
            mime="application/json",
            key=f"{cur.id}-download-json",
            icon=":material/download:",
            on_click="ignore",
        )
        if csv_matches(csv_path, exported["exported_at"]):
            st.download_button(
                "CSV herunterladen",
                data=csv_path.read_bytes(),
                file_name=csv_path.name,
                mime="text/csv",
                key=f"{cur.id}-download-csv",
                icon=":material/download:",
                on_click="ignore",
            )
        else:
            st.warning(
                "Die CSV-Datei fehlt oder stammt aus einem anderen Export. Bitte neu exportieren.",
                icon=ui.WARNING,
            )


def csv_matches(path: Path, exported_at: str) -> bool:
    if not path.exists():
        return False
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return all(
            row["exportiert_am"] == exported_at for row in csv.DictReader(handle)
        )


def verify_section(cur: Current, state: str, result: dict | None, approved: bool):
    ui.section("Export prüfen")
    st.caption(
        "Liest die gespeicherte JSON-Datei erneut ein und vergleicht sie mit dem Arbeitsstand."
    )
    if st.button(
        "Export erneut laden und prüfen",
        key=f"{cur.id}-roundtrip",
        disabled=state != "current",
        type="primary" if state == "current" and result is None else "secondary",
        icon=":material/fact_check:",
    ):
        with st.spinner("Export wird gelesen und verglichen …"):
            actions.run_roundtrip(cur.id)
        st.rerun()
    if state != "current":
        reason = (
            "Erst exportieren." if state == "none" else "Bitte zuerst neu exportieren."
        )
        st.caption(f"{ui.LOCK} Noch nicht möglich: {reason}")
    elif result is None:
        st.caption(
            "Noch nicht geprüft. Prüfergebnisse gelten für diese Sitzung; nach einem Neustart "
            "der Anwendung ist eine neue Prüfung nötig."
        )
    else:
        verification_result(cur, result, approved)


def verification_result(cur: Current, result: dict, approved: bool):
    total = len(result["report"])
    failed = [label for label, ok in result["report"] if not ok]
    checked = ui.local_time_exact(result["checked_at"])
    if passed(result):
        st.success(
            "Export geprüft: Die zurückgelesenen Daten stimmen mit dem Arbeitsstand überein.",
            icon=ui.CONFIRMED,
        )
        st.markdown(f"Geprüft {checked} · {total} von {total} Prüfpunkten erhalten.")
    else:
        st.error(
            f"Prüfung fehlgeschlagen: {len(failed) or 'Einzelne'} von {total} Prüfpunkten weichen "
            "ab. Wurde die Datei außerhalb der Anwendung verändert? Nächster Schritt: neu "
            "exportieren und erneut prüfen.",
            icon=ui.ERROR,
        )
        st.markdown(f"Geprüft {checked}.")
    st.caption(
        "Verglichen wird die JSON-Datei mit dem gespeicherten Arbeitsstand. Die CSV-Datei wird "
        "dabei nicht zurückgelesen, und über die fachliche Richtigkeit der Entscheidungen sagt "
        "die Prüfung nichts."
    )
    with st.expander("Einzelergebnisse", expanded=not passed(result)):
        for label, ok in result["report"]:
            if ok:
                st.success(f"Erhalten: {label}", icon=ui.OK)
            else:
                st.error(f"Abweichung: {label}", icon=ui.ERROR)
        if result["differing"]:
            st.markdown(
                "Abweichende Felder im Export:\n"
                + "\n".join(f"- `{p}`" for p in result["differing"])
            )
    if not passed(result):
        return
    if approved:
        st.button(
            "Weiter: zurück zur Sammlung",
            key=f"{cur.id}-export-continue",
            type="primary",
            icon=":material/arrow_forward:",
            on_click=actions.open_object,
            args=("sammlung",),
        )
    else:
        st.caption("Der Export ist geprüft, das Objekt aber noch nicht endbestätigt.")
        workflow.continue_button(cur.id, cur.record, f"{cur.id}-export-continue")


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
