"""Volltextsuche über die Sammlung. Nur casefold, keine Normalisierung typografischer Varianten."""

from kinderbuch_bildlabor import second_review, workflow

STATUSES = ("offen", "strittig", "endbestätigt")


def status(record: dict) -> str:
    if workflow.approved(record):
        counts = second_review.summary(record)
        return "strittig" if counts and counts["disagree"] else "endbestätigt"
    return "offen"


def fields(record: dict) -> list[tuple[str, str]]:
    biblio = record["bibliographic_metadata_from_colibri"]
    found = [("Titel", biblio["title"]), ("Autor", biblio.get("author_display") or "")]
    found.append(
        ("Beschreibung", record["image_description"]["working_description_de"])
    )
    for region in record["region_annotations"]:
        found += [("Suchbegriff", k) for k in region.get("keywords_de", [])]
    found += [
        ("Transkription", v)
        for k, v in (record.get("transcription") or {}).items()
        if isinstance(v, str)
    ]
    return found


def search(
    records: dict[str, dict], query: str, wanted: tuple[str, ...]
) -> list[tuple[str, str, str]]:
    """(Objekt, Feld, Text) je Treffer; leere Anfrage trifft alle Objekte im Statusfilter."""
    needle = query.strip().casefold()
    hits = []
    for object_id, record in records.items():
        if status(record) not in wanted:
            continue
        if not needle:
            hits.append((object_id, "", ""))
            continue
        hits += [
            (object_id, name, text)
            for name, text in fields(record)
            if needle in text.casefold()
        ]
    return hits
