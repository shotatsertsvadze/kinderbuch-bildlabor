"""Speichern und Bestätigen aus der Oberfläche.

Jede Aktion nennt ihr Objekt ausdrücklich, liest den gespeicherten Stand, ändert ihn und
speichert nur echte Änderungen. Eingaben in dieser Sitzung liegen in st.session_state.
"""

import hashlib
from pathlib import Path

import streamlit as st

from kinderbuch_bildlabor import export, review, store, ui, validate


def reviewer() -> str:
    return st.session_state.get("reviewer", "").strip()


FIELD_LABELS = {
    "working_title": "Bildtitel",
    "working_publisher_statement": "Verlagsangabe auf dem Bildblatt",
}


def region_label(object_id: str, region_id: str) -> str:
    record = store.read_json(store.object_source(object_id).record)
    return f"„{review.find_region(record, region_id)['label_de']}“"


def write_failed(error: OSError) -> None:
    where = f" ({Path(error.filename).name})" if error.filename else ""
    st.session_state.notice = (
        f"Schreiben fehlgeschlagen: {error.strerror}{where}. "
        "Bitte Berechtigungen und freien Speicherplatz prüfen und erneut versuchen."
    )


DRAFT_NEXT_DE = (
    "Das ist noch keine Prüfung: Der Bereich gilt als ungeprüft, bis Sie ihn mit Häkchen und "
    "Bestätigungsknopf bestätigen."
)


def apply(object_id: str, area_de: str, change, *args, slot: str | None = None) -> None:
    """Speichert über die Speichersperre; mit `slot` bleibt das Ergebnis am Knopf sichtbar."""
    src = store.object_source(object_id)
    try:
        changed = store.update_working_copy(
            src, lambda record: change(record, *args), area_de
        )
    except review.ContentChanged as error:
        st.session_state.notice = str(error)
        return
    except OSError as error:
        write_failed(error)
        return
    if slot is None:
        if changed:
            # Eine Bestätigung überholt den Entwurfshinweis
            st.session_state.pop("feedback", None)
        return
    if changed:
        ui.set_feedback(
            object_id, slot, "draft", f"Entwurf gespeichert: {area_de}. {DRAFT_NEXT_DE}"
        )
    else:
        ui.set_feedback(
            object_id,
            slot,
            "info",
            f"Nichts gespeichert: {area_de} entspricht bereits dem gespeicherten Stand.",
        )


def xywh_keys(region_id: str) -> list[str]:
    return [f"{region_id}-{k}" for k in "xywh"]


def input_xywh(region_id: str) -> list[int]:
    return [int(st.session_state[key]) for key in xywh_keys(region_id)]


def save_coordinates(object_id: str, region_id: str) -> None:
    apply(
        object_id,
        f"Koordinaten {region_label(object_id, region_id)}",
        review.set_region_xywh,
        region_id,
        input_xywh(region_id),
        ui.seen_values(xywh_keys(region_id)),
        slot=f"{region_id}-save",
    )


def confirm_region(object_id: str, region_id: str, seen_xywh: list[int]) -> None:
    apply(
        object_id,
        f"Bestätigung Regionsgrenzen {region_label(object_id, region_id)}",
        review.confirm_region,
        region_id,
        reviewer(),
        seen_xywh,
    )


def keyword_list(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def keyword_key(region_id: str) -> str:
    return f"{region_id}-keywords"


def save_keywords(object_id: str, region_id: str) -> None:
    key = keyword_key(region_id)
    apply(
        object_id,
        "Suchbegriffe",
        review.set_keywords,
        region_id,
        keyword_list(st.session_state[key]),
        keyword_list(ui.seen_values([key])[0]),
        slot=f"{key}-save",
    )


def confirm_keywords(object_id: str, region_id: str, seen: list[str]) -> None:
    apply(
        object_id,
        "Bestätigung Suchbegriffe",
        review.confirm_keywords,
        region_id,
        reviewer(),
        seen,
    )


def description_key(object_id: str) -> str:
    return f"{object_id}-description"


def save_description(object_id: str) -> None:
    key = description_key(object_id)
    apply(
        object_id,
        "Bildbeschreibung",
        review.set_description,
        st.session_state[key].strip(),
        ui.seen_values([key])[0],
        slot=f"{key}-save",
    )


def confirm_description(object_id: str, seen_text: str) -> None:
    apply(
        object_id,
        "Bestätigung Bildbeschreibung",
        review.confirm_description,
        reviewer(),
        seen_text,
    )


def transcription_key(object_id: str, field: str) -> str:
    return f"{object_id}-{field}"


def save_transcription(object_id: str, field: str) -> None:
    key = transcription_key(object_id, field)
    apply(
        object_id,
        f"Transkription {FIELD_LABELS[field]}",
        review.set_transcription,
        field,
        st.session_state[key],
        ui.seen_values([key])[0],
        slot=f"{key}-save",
    )


def confirm_transcription(object_id: str, field: str, seen_text: str) -> None:
    apply(
        object_id,
        f"Bestätigung Transkription {FIELD_LABELS[field]}",
        review.confirm_transcription,
        field,
        reviewer(),
        seen_text,
    )


def export_paths(object_id: str):
    return store.EXPORT_DIR / f"{object_id}.json", store.EXPORT_DIR / f"{object_id}.csv"


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def roundtrip_key(object_id: str) -> str:
    return f"{object_id}-roundtrip-result"


def run_export(object_id: str) -> bool:
    json_path, csv_path = export_paths(object_id)
    previous = st.session_state.get(roundtrip_key(object_id))
    current = store.load_working_copy(store.object_source(object_id))
    try:
        data = export.export_json(current, json_path)
        export.export_csv(current["record"], data["exported_at"], csv_path)
    except OSError as error:
        write_failed(error)
        return False
    st.session_state.pop(roundtrip_key(object_id), None)
    # Eine frühere Prüfung galt der alten Datei; das soll sichtbar erklärt werden
    st.session_state[f"{object_id}-export-replaced"] = (
        data["exported_at"],
        previous["exported_at"] if previous else None,
    )
    return True


def run_roundtrip(object_id: str) -> None:
    json_path, _ = export_paths(object_id)
    exported = store.read_json(json_path)
    current = store.load_working_copy(store.object_source(object_id))["record"]
    st.session_state[roundtrip_key(object_id)] = {
        "exported_at": exported["exported_at"],
        "digest": file_digest(json_path),
        "checked_at": store.now_utc(),
        "report": export.roundtrip_report(current, exported["record"]),
        "differing": export.differing_fields(current, exported["record"]),
    }


COLLECTION_CSV = "sammlung.csv"


def run_collection_export() -> None:
    records = [store.load_working_copy(src)["record"] for src in store.catalog()]
    try:
        export.export_collection_csv(
            records, store.now_utc(), store.EXPORT_DIR / COLLECTION_CSV
        )
    except OSError as error:
        write_failed(error)
        return
    st.toast("Exportiert: Sammlungsübersicht als CSV", icon=ui.OK)


def open_object(object_id: str) -> None:
    st.session_state.view = object_id


def current_findings(src: store.ObjectSource, record: dict) -> list:
    """Validierung des gerade geladenen Stands; nur unter der Speichersperre aufrufen."""
    working = store.load_working_copy(src)
    working["record"] = record
    collection = [
        record if other.id == src.id else store.load_working_copy(other)["record"]
        for other in store.catalog()
    ]
    return validate.run_all(working, src, collection)


def approve_object(object_id: str, seen: dict, acknowledged: bool) -> None:
    src = store.object_source(object_id)

    def approve(record):
        findings = current_findings(src, record)
        return review.approve_final(record, seen, reviewer(), acknowledged, findings)

    try:
        store.update_working_copy(src, approve, "Endbestätigung")
    except (review.ContentChanged, review.ApprovalBlocked) as error:
        st.session_state.notice = str(error)
    except OSError as error:
        write_failed(error)


def decision_key(object_id: str, code: str, message: str) -> str:
    digest = hashlib.sha256(message.encode()).hexdigest()[:8]
    return f"{object_id}-decision-{code}-{digest}"


def reconfirm_decision(object_id: str, code: str, message: str, seen: dict) -> None:
    key = decision_key(object_id, code, message)
    try:
        store.update_working_copy(
            store.object_source(object_id),
            lambda record: review.reconfirm_decision(
                record, code, message, reviewer(), seen
            ),
            "Entscheidung erneut bestätigt",
        )
    except (review.ContentChanged, review.DecisionInvalid) as error:
        st.session_state[f"{key}-error"] = str(error)
        return
    except OSError as error:
        write_failed(error)
        return
    # Häkchen sichtbar zurücksetzen: jede erneute Bestätigung muss bewusst neu ausgelöst werden
    st.session_state[f"{key}-reconfirm-check"] = False
    ui.set_feedback(
        object_id,
        key,
        "info",
        f"Entscheidung unverändert erneut bestätigt von {reviewer()}. Frühere Einträge bleiben "
        "im Prüfprotokoll. Eine bisherige Endbestätigung ist aufgehoben und der Export veraltet; "
        "nächster Schritt: Endbestätigung im Reiter „Prüfung“ neu erteilen, dann exportieren.",
    )


def record_decision(object_id: str, code: str, message: str, seen_basis) -> None:
    key = decision_key(object_id, code, message)
    src = store.object_source(object_id)

    def decide(record):
        findings = current_findings(src, record)
        if not any(
            f.code == code and f.message_de == message and validate.decidable(record, f)
            for f in findings
        ):
            raise review.ContentChanged(
                "Der Hinweis hat sich inzwischen geändert. Bitte den aktuellen Stand ansehen."
            )
        return review.record_decision(
            record,
            code,
            message,
            st.session_state.get(f"{key}-outcome"),
            st.session_state.get(f"{key}-rationale", ""),
            reviewer(),
            seen_basis,
        )

    try:
        changed = store.update_working_copy(src, decide, "Begründete Entscheidung")
    except (review.ContentChanged, review.DecisionInvalid) as error:
        st.session_state[f"{key}-error"] = str(error)
        return
    except OSError as error:
        write_failed(error)
        return
    for suffix in ("outcome", "rationale"):
        st.session_state.pop(f"{key}-{suffix}", None)
    if not changed:
        ui.set_feedback(
            object_id,
            key,
            "info",
            "Nichts gespeichert: Entscheidung und Begründung sind unverändert.",
        )
