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

STATUS_LABELS_DE = {
    REGION_DRAFT: "Entwurf – visuelle Prüfung offen",
    REGION_REVIEWED: "Grenzen visuell geprüft",
    KEYWORDS_ACCEPTED: "vom Nutzer akzeptiert",
    KEYWORDS_EDITED: "geändert – erneute Prüfung offen",
    KEYWORDS_PROPOSED: "Vorschlag – Prüfung offen",
    DESCRIPTION_REVIEWED: "am Bild geprüft",
    TRANSCRIPTION_PROVISIONAL: "vorläufig",
    TRANSCRIPTION_REVIEWED: "geprüft – nicht als Ground Truth freigegeben",
    "unreviewed": "ungeprüft",
    "draft_pending_final_review": "Entwurf – Endprüfung offen",
}


DONE_STATUSES = {REGION_REVIEWED, KEYWORDS_ACCEPTED, TRANSCRIPTION_REVIEWED, DESCRIPTION_REVIEWED}


def status_label(status: str) -> str:
    return STATUS_LABELS_DE.get(status, status)


def review_areas(record: dict) -> list[dict]:
    """Alle einzeln bestätigbaren Prüfbereiche in Arbeitsreihenfolge."""
    areas = [{"label_de": f"Regionsgrenzen: {r['label_de']}", "status": r["review_status"], "tab_de": "Regionen"}
             for r in record["region_annotations"]]
    areas.append({"label_de": "Bildbeschreibung", "status": record["image_description"]["review_status"],
                  "tab_de": "Beschreibung"})
    areas += [{"label_de": f"Suchbegriffe: {r['label_de']}", "status": r["keyword_review_status"],
               "tab_de": "Beschreibung"}
              for r in record["region_annotations"] if "keywords_de" in r]
    areas += [{"label_de": f"Transkription: {r['label_de']}",
               "status": record["transcription"]["review_status_by_field"][r["transcription_field"]],
               "tab_de": "Transkription"}
              for r in record["region_annotations"] if r.get("transcription_field")]
    for area in areas:
        area["done"] = area["status"] in DONE_STATUSES
    return areas


def last_confirmation(record: dict, area: str) -> dict | None:
    """Letzter Protokolleintrag mit Person für diesen Bereich."""
    entries = [e for e in record.get("review_log", []) if e["area"] == area and "by" in e]
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
        raise ContentChanged(f"{what_de} wurde inzwischen an anderer Stelle geändert. "
                             "Bitte den aktuellen Stand ansehen und erneut bestätigen.")


def set_region_xywh(record: dict, region_id: str, xywh: list[int], seen_xywh: list[int]) -> bool:
    region = find_region(record, region_id)
    if region["xywh"] == xywh:
        return False
    require_seen(region["xywh"], seen_xywh, f"Die Region {region_id}")
    region["xywh"] = xywh
    region["review_status"] = REGION_DRAFT
    log(record, region_id, "Koordinaten geändert; Status auf Entwurf zurückgesetzt")
    return True


def confirm_region(record: dict, region_id: str, by: str, seen_xywh: list[int]) -> bool:
    region = find_region(record, region_id)
    require_seen(region["xywh"], seen_xywh, f"Die Region {region_id}")
    region["review_status"] = REGION_REVIEWED
    log(record, region_id, "Regionsgrenzen visuell bestätigt", by)
    return True


def set_keywords(record: dict, region_id: str, keywords: list[str], seen_keywords: list[str]) -> bool:
    region = find_region(record, region_id)
    if region["keywords_de"] == keywords:
        return False
    require_seen(region["keywords_de"], seen_keywords, "Die Suchbegriffe")
    region["keywords_de"] = keywords
    region["keyword_review_status"] = KEYWORDS_EDITED
    log(record, f"{region_id}/keywords_de", "Suchbegriffe geändert; Prüfung zurückgesetzt")
    return True


def confirm_keywords(record: dict, region_id: str, by: str, seen_keywords: list[str]) -> bool:
    region = find_region(record, region_id)
    require_seen(region["keywords_de"], seen_keywords, "Die Suchbegriffe")
    region["keyword_review_status"] = KEYWORDS_ACCEPTED
    log(record, f"{region_id}/keywords_de", "Suchbegriffe bestätigt", by)
    return True


def set_description(record: dict, text: str, seen_text: str) -> bool:
    description = record["image_description"]
    if description["working_description_de"] == text:
        return False
    require_seen(description["working_description_de"], seen_text, "Die Arbeitsbeschreibung")
    description["working_description_de"] = text
    description["review_status"] = DESCRIPTION_OPEN
    log(record, "image_description", "Arbeitsbeschreibung geändert; Prüfung zurückgesetzt")
    return True


def confirm_description(record: dict, by: str, seen_text: str) -> bool:
    description = record["image_description"]
    require_seen(description["working_description_de"], seen_text, "Die Arbeitsbeschreibung")
    description["review_status"] = DESCRIPTION_REVIEWED
    log(record, "image_description", "Bildbeschreibung am Bild bestätigt", by)
    return True


def set_transcription(record: dict, field: str, text: str, seen_text: str) -> bool:
    transcription = record["transcription"]
    if transcription[field] == text:
        return False
    require_seen(transcription[field], seen_text, "Die Transkription")
    transcription[field] = text
    transcription["review_status_by_field"][field] = TRANSCRIPTION_PROVISIONAL
    log(record, f"transcription/{field}", "Transkription geändert; Status auf vorläufig gesetzt")
    return True


def confirm_transcription(record: dict, field: str, by: str, seen_text: str) -> bool:
    transcription = record["transcription"]
    require_seen(transcription[field], seen_text, "Die Transkription")
    transcription["review_status_by_field"][field] = TRANSCRIPTION_REVIEWED
    log(record, f"transcription/{field}", "Transkription geprüft (keine Ground-Truth-Freigabe)", by)
    return True
