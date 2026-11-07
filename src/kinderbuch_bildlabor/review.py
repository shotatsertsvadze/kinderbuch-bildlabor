"""Bearbeitungen und ausdrückliche Prüfbestätigungen.

Jeder Prüfbereich hat einen eigenen Status. Eine Änderung am Inhalt setzt nur den
Status dieses Bereichs zurück, weil die alte Bestätigung den neuen Inhalt nicht deckt.
Bestätigungen werden mit Person und Zeitpunkt im review_log festgehalten.
"""

from kinderbuch_bildlabor.store import now_utc

REGION_DRAFT = "draft_pending_visual_review"
REGION_REVIEWED = "visually_reviewed"
KEYWORDS_ACCEPTED = "accepted_by_user"
KEYWORDS_EDITED = "edited_pending_review"
KEYWORDS_PROPOSED = "proposed_unreviewed"
DESCRIPTION_OPEN = "unreviewed"
DESCRIPTION_REVIEWED = "description_reviewed"
TRANSCRIPTION_PROVISIONAL = "provisional"
TRANSCRIPTION_REVIEWED = "reviewed"
CLASSIFICATION_OPEN = "classification_open"
CLASSIFICATION_UNDECIDABLE = "classification_undecidable"
CLASSIFICATION_DECIDED = "classification_decided"

STATUS_LABELS_DE = {
    REGION_DRAFT: "Entwurf – visuelle Prüfung offen",
    REGION_REVIEWED: "Grenzen visuell geprüft",
    KEYWORDS_ACCEPTED: "vom Nutzer akzeptiert",
    KEYWORDS_EDITED: "geändert – erneute Prüfung offen",
    KEYWORDS_PROPOSED: "Vorschlag – Prüfung offen",
    DESCRIPTION_REVIEWED: "am Bild geprüft",
    TRANSCRIPTION_PROVISIONAL: "vorläufig",
    TRANSCRIPTION_REVIEWED: "geprüft – nicht als Ground Truth freigegeben",
    CLASSIFICATION_OPEN: "Entscheidung am Bild offen",
    CLASSIFICATION_UNDECIDABLE: "begründet als nicht entscheidbar festgehalten",
    CLASSIFICATION_DECIDED: "begründet entschieden",
    "unreviewed": "ungeprüft",
    "draft_pending_final_review": "Entwurf – Endbestätigung offen",
}


DONE_STATUSES = {
    REGION_REVIEWED,
    KEYWORDS_ACCEPTED,
    TRANSCRIPTION_REVIEWED,
    DESCRIPTION_REVIEWED,
    CLASSIFICATION_DECIDED,
}


def status_label(status: str) -> str:
    return STATUS_LABELS_DE.get(status, status)


def origin_label(text: str | None) -> str | None:
    if text is None:
        return None
    return text.removesuffix("; ungeprüft").removesuffix(", ungeprüft")


def review_areas(record: dict) -> list[dict]:
    """Alle einzeln bestätigbaren Prüfbereiche in Arbeitsreihenfolge."""
    areas = [
        {
            "label_de": f"Regionsgrenzen: {r['label_de']}",
            "status": r["review_status"],
            "tab_de": "Regionen",
        }
        for r in record["region_annotations"]
    ]
    if message := classification_message(record):
        areas.append(
            {
                "label_de": "Bildklassifikation (Colibri manuell gegen automatisch)",
                "status": classification_status(record, message),
                "tab_de": "Klassifikation",
            }
        )
    areas.append(
        {
            "label_de": "Bildbeschreibung",
            "status": record["image_description"]["review_status"],
            "tab_de": "Beschreibung",
        }
    )
    areas += [
        {
            "label_de": f"Suchbegriffe: {r['label_de']}",
            "status": r["keyword_review_status"],
            "tab_de": "Beschreibung",
        }
        for r in record["region_annotations"]
        if "keywords_de" in r
    ]
    areas += [
        {
            "label_de": f"Transkription: {r['label_de']}",
            "status": record["transcription"]["review_status_by_field"][
                r["transcription_field"]
            ],
            "tab_de": "Transkription",
        }
        for r in record["region_annotations"]
        if r.get("transcription_field")
    ]
    for area in areas:
        area["done"] = area["status"] in DONE_STATUSES
    return areas


def last_confirmation(record: dict, area: str) -> dict | None:
    """Letzter Protokolleintrag mit Person für diesen Bereich."""
    entries = [
        e for e in record.get("review_log", []) if e["area"] == area and "by" in e
    ]
    return entries[-1] if entries else None


def find_region(record: dict, region_id: str) -> dict:
    return next(r for r in record["region_annotations"] if r["id"] == region_id)


def log(record: dict, area: str, action: str, by: str | None = None) -> None:
    entry = {"at": now_utc(), "area": area, "action": action}
    if by is not None:
        entry["by"] = by
    record.setdefault("review_log", []).append(entry)


class ContentChanged(Exception):
    """Der bestätigte Inhalt ist nicht mehr der gespeicherte (z. B. in einem anderen Tab geändert)."""


def require_seen(saved, seen, what_de: str) -> None:
    if saved != seen:
        raise ContentChanged(
            f"{what_de} wurde inzwischen an anderer Stelle geändert. "
            "Bitte den aktuellen Stand ansehen und erneut bestätigen."
        )


def set_region_xywh(
    record: dict, region_id: str, xywh: list[int], seen_xywh: list[int]
) -> bool:
    region = find_region(record, region_id)
    if region["xywh"] == xywh:
        return False
    require_seen(region["xywh"], seen_xywh, f"Die Region {region_id}")
    invalidate_final(record)
    region["xywh"] = xywh
    region["review_status"] = REGION_DRAFT
    log(record, region_id, "Koordinaten geändert; Status auf Entwurf zurückgesetzt")
    drop_stale_decisions(record)
    return True


def confirm_region(record: dict, region_id: str, by: str, seen_xywh: list[int]) -> bool:
    region = find_region(record, region_id)
    require_seen(region["xywh"], seen_xywh, f"Die Region {region_id}")
    region["review_status"] = REGION_REVIEWED
    log(record, region_id, "Regionsgrenzen visuell bestätigt", by)
    return True


def set_keywords(
    record: dict, region_id: str, keywords: list[str], seen_keywords: list[str]
) -> bool:
    region = find_region(record, region_id)
    if region["keywords_de"] == keywords:
        return False
    require_seen(region["keywords_de"], seen_keywords, "Die Suchbegriffe")
    invalidate_final(record)
    region["keywords_de"] = keywords
    region["keyword_review_status"] = KEYWORDS_EDITED
    log(
        record,
        f"{region_id}/keywords_de",
        "Suchbegriffe geändert; Prüfung zurückgesetzt",
    )
    return True


def confirm_keywords(
    record: dict, region_id: str, by: str, seen_keywords: list[str]
) -> bool:
    region = find_region(record, region_id)
    require_seen(region["keywords_de"], seen_keywords, "Die Suchbegriffe")
    region["keyword_review_status"] = KEYWORDS_ACCEPTED
    log(record, f"{region_id}/keywords_de", "Suchbegriffe bestätigt", by)
    return True


def set_description(record: dict, text: str, seen_text: str) -> bool:
    description = record["image_description"]
    if description["working_description_de"] == text:
        return False
    require_seen(
        description["working_description_de"], seen_text, "Die Arbeitsbeschreibung"
    )
    invalidate_final(record)
    description["working_description_de"] = text
    description["review_status"] = DESCRIPTION_OPEN
    log(
        record,
        "image_description",
        "Arbeitsbeschreibung geändert; Prüfung zurückgesetzt",
    )
    return True


def confirm_description(record: dict, by: str, seen_text: str) -> bool:
    description = record["image_description"]
    require_seen(
        description["working_description_de"], seen_text, "Die Arbeitsbeschreibung"
    )
    description["review_status"] = DESCRIPTION_REVIEWED
    log(record, "image_description", "Bildbeschreibung am Bild bestätigt", by)
    return True


def set_transcription(record: dict, field: str, text: str, seen_text: str) -> bool:
    transcription = record["transcription"]
    if transcription[field] == text:
        return False
    require_seen(transcription[field], seen_text, "Die Transkription")
    invalidate_final(record)
    transcription[field] = text
    transcription["review_status_by_field"][field] = TRANSCRIPTION_PROVISIONAL
    log(
        record,
        f"transcription/{field}",
        "Transkription geändert; Status auf vorläufig gesetzt",
    )
    drop_stale_decisions(record)
    return True


def confirm_transcription(record: dict, field: str, by: str, seen_text: str) -> bool:
    transcription = record["transcription"]
    require_seen(transcription[field], seen_text, "Die Transkription")
    transcription["review_status_by_field"][field] = TRANSCRIPTION_REVIEWED
    log(
        record,
        f"transcription/{field}",
        "Transkription geprüft (keine Ground-Truth-Freigabe)",
        by,
    )
    return True


FINAL_APPROVED = "final_review_approved"


class ApprovalBlocked(ValueError):
    pass


def invalidate_final(record: dict) -> None:
    if (
        record.pop("final_approval", None) is not None
        or record.get("status") == FINAL_APPROVED
    ):
        record["status"] = "draft_pending_final_review"
        log(record, "final_review", "Endbestätigung durch Inhaltsänderung aufgehoben")


def readiness(record: dict, findings: list) -> str:
    from kinderbuch_bildlabor.validate import approval_blockers

    if approval_blockers(findings) or not all(a["done"] for a in review_areas(record)):
        return "Offen"
    if record.get("final_approval") and record.get("status") == FINAL_APPROVED:
        return "Endbestätigt"
    return "Bereit zur Endbestätigung"


def approve_final(
    record: dict, seen: dict, by: str, acknowledged: bool, findings: list
) -> bool:
    require_seen(record, seen, "Das Objekt")
    if not by.strip() or not acknowledged:
        raise ApprovalBlocked("Name und ausdrückliche Bestätigung sind erforderlich.")
    if readiness(record, findings) == "Offen":
        raise ApprovalBlocked(
            "Offene Prüfbereiche oder blockierende Befunde verhindern die Endbestätigung."
        )
    if record.get("final_approval"):
        return False
    record["status"] = FINAL_APPROVED
    record["final_approval"] = {"by": by.strip(), "at": now_utc()}
    log(
        record,
        "final_review",
        "Endbestätigung des Objekts erteilt (keine Ground-Truth-Freigabe)",
        by.strip(),
    )
    return True


# Begründete Entscheidungen zu fachlichen Hinweisen. Der Hinweis bleibt sichtbar; eine
# Entscheidung gilt nur für genau diesen Hinweistext und den Inhalt, auf dem sie beruht.
CLASSIFICATION = "CLASSIFICATION_DIFFERENCE"
UNDECIDABLE = "Nicht entscheidbar; bleibt offen"


class DecisionInvalid(ValueError):
    pass


def classification_labels(record: dict) -> tuple[str, str] | None:
    source = record["source"]
    manual = source.get("colibri_groundtruth")
    automatic = source.get("colibri_classification")
    if manual and automatic and manual != automatic:
        return manual, automatic
    return None


def classification_message(record: dict) -> str | None:
    labels = classification_labels(record)
    if not labels:
        return None
    return (
        f"Bildklassifikation in Colibri abweichend: manuell „{labels[0]}“, "
        f"automatisch „{labels[1]}“."
    )


def decision_options(code: str, record: dict) -> list[str]:
    if code == CLASSIFICATION:
        labels = classification_labels(record)
        assert labels
        return [
            f"Manuelle Klasse trifft zu: {labels[0]}",
            f"Automatische Klasse trifft zu: {labels[1]}",
            "Keine der beiden Klassen trifft zu",
            UNDECIDABLE,
        ]
    if code == "ILLUSTRATOR_ATTRIBUTION":
        return ["Illustrator bleibt unbekannt; Feld bewusst leer", UNDECIDABLE]
    return [
        "Unterschied geprüft; beide Angaben bleiben mit ihrem Bezug erhalten",
        UNDECIDABLE,
    ]


def decision_basis(record: dict, code: str):
    """Inhalt, auf dem eine Entscheidung beruht; ändert er sich, verfällt sie."""
    if code == CLASSIFICATION:
        return [
            r["xywh"]
            for r in record["region_annotations"]
            if r["region_type"] == "illustration"
        ]
    if code == "IMPRINT_CONTEXT":
        return (record.get("transcription") or {}).get("working_publisher_statement")
    if code == "ILLUSTRATOR_ATTRIBUTION":
        return record["image_description"]["illustrator"]
    return None


def decision_key(code: str, message: str) -> str:
    return f"{code}: {message}"


def decision(record: dict, code: str, message: str) -> dict | None:
    return record.get("decisions", {}).get(decision_key(code, message))


def resolves(entry: dict | None) -> bool:
    return entry is not None and entry["outcome_de"] != UNDECIDABLE


def classification_status(record: dict, message: str) -> str:
    entry = decision(record, CLASSIFICATION, message)
    if entry is None:
        return CLASSIFICATION_OPEN
    return CLASSIFICATION_DECIDED if resolves(entry) else CLASSIFICATION_UNDECIDABLE


def record_decision(
    record: dict,
    code: str,
    message: str,
    outcome: str | None,
    rationale: str,
    by: str,
    seen_basis,
) -> bool:
    if not by.strip():
        raise DecisionInvalid(
            "Tragen Sie im Prüfpfad unter „Prüfende Person“ Ihren Namen ein."
        )
    if outcome not in decision_options(code, record):
        raise DecisionInvalid("Bitte eine Entscheidung auswählen.")
    if not rationale.strip():
        raise DecisionInvalid("Bitte die Entscheidung begründen.")
    basis = decision_basis(record, code)
    require_seen(basis, seen_basis, "Der zugrunde liegende Inhalt")
    old = decision(record, code, message)
    if (
        old
        and old["outcome_de"] == outcome
        and old["rationale_de"] == rationale.strip()
    ):
        return False
    invalidate_final(record)
    record.setdefault("decisions", {})[decision_key(code, message)] = {
        "code": code,
        "finding_de": message,
        "outcome_de": outcome,
        "rationale_de": rationale.strip(),
        "basis": basis,
        "by": by.strip(),
        "at": now_utc(),
    }
    log(
        record,
        f"decision/{code}",
        f"Entscheidung: {outcome}. Begründung: {rationale.strip()}",
        by.strip(),
    )
    return True


def drop_stale_decisions(record: dict) -> None:
    """Nach einer Inhaltsänderung: Entscheidungen auf altem Inhalt aufheben, Protokoll behalten."""
    decisions = record.get("decisions", {})
    for key, entry in list(decisions.items()):
        if entry["basis"] != decision_basis(record, entry["code"]):
            del decisions[key]
            log(
                record,
                f"decision/{entry['code']}",
                "Entscheidung durch Inhaltsänderung aufgehoben "
                f"(war: {entry['outcome_de']}; von {entry['by']})",
            )
