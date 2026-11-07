"""Prüfungen eines Datensatzes, getrennt nach drei Kategorien.

- technischer Fehler: Daten sind formal unbrauchbar oder widersprüchlich
- fachlicher Prüfhinweis: eine fachliche Entscheidung steht noch aus
- nicht ausgeführte Prüfung: wurde bewusst noch nicht gemacht, Ergebnis unbekannt
- begründet entschieden: fachlicher Hinweis mit Entscheidung einer benannten Person; bleibt sichtbar

Unbekannte optionale Angaben (z. B. Illustrator) erzeugen keinen Fehler.
"""

import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from PIL import Image

from kinderbuch_bildlabor import oai, regions, review, store

TECHNICAL = "technischer_fehler"
REVIEW = "fachlicher_hinweis"
NOT_RUN = "nicht_ausgefuehrt"
DOCUMENTED = "begruendet_entschieden"

CATEGORY_LABELS_DE = {
    TECHNICAL: "Technische Fehler",
    REVIEW: "Fachliche Prüfhinweise",
    NOT_RUN: "Noch nicht ausgeführte Prüfungen",
    DOCUMENTED: "Begründet entschiedene Hinweise",
}

REQUIRED_FIELDS = [
    ("id",),
    ("source", "institution"),
    ("source", "ppn"),
    ("source", "physical_page_id"),
    ("source", "image_width"),
    ("source", "image_height"),
    ("source", "viewer_url"),
    ("source", "colibri_dataset_license"),
    ("source", "colibri_dataset_credit"),
    ("bibliographic_metadata_from_colibri", "title"),
    ("bibliographic_metadata_from_colibri", "rights_statement"),
    ("image_description", "working_description_de"),
]
REQUIRED_REGION_FIELDS = [
    "id",
    "label_de",
    "region_type",
    "xywh",
    "coordinate_unit",
    "review_status",
]
OPTIONAL_UNKNOWN_FIELDS = [
    (("image_description", "illustrator"), "Illustrator"),
    (("source", "printed_page_number"), "Gedruckte Seitenzahl"),
]


@dataclass(frozen=True)
class Finding:
    category: str
    code: str
    message_de: str


def get_path(data: dict, path: tuple):
    for key in path:
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def is_missing(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def check_required(record: dict) -> list[Finding]:
    findings = [
        Finding(TECHNICAL, "MISSING_FIELD", f"Pflichtangabe fehlt: {'.'.join(path)}")
        for path in REQUIRED_FIELDS
        if is_missing(get_path(record, path))
    ]
    for region in record.get("region_annotations", []):
        for field in REQUIRED_REGION_FIELDS:
            if is_missing(region.get(field)):
                findings.append(
                    Finding(
                        TECHNICAL,
                        "MISSING_REGION_FIELD",
                        f"Region {region.get('id', '?')}: Pflichtangabe fehlt: {field}",
                    )
                )
    return findings


def check_duplicate_ids(records: list[dict]) -> list[Finding]:
    object_ids = Counter(r.get("id") for r in records)
    region_ids = Counter(
        g.get("id") for r in records for g in r.get("region_annotations", [])
    )
    return [
        Finding(
            TECHNICAL, "DUPLICATE_OBJECT_ID", f"Objekt-ID mehrfach vergeben: {i} ({n}×)"
        )
        for i, n in object_ids.items()
        if n > 1
    ] + [
        Finding(
            TECHNICAL,
            "DUPLICATE_REGION_ID",
            f"Regions-ID mehrfach vergeben: {i} ({n}×)",
        )
        for i, n in region_ids.items()
        if n > 1
    ]


def check_regions(record: dict) -> list[Finding]:
    width, height = record["source"]["image_width"], record["source"]["image_height"]
    findings = []
    for region in record["region_annotations"]:
        if region.get("coordinate_unit") != "pixel":
            findings.append(
                Finding(
                    TECHNICAL,
                    "REGION_UNIT",
                    f"Region {region['id']}: Koordinateneinheit ist nicht 'pixel'.",
                )
            )
        for problem in regions.bounds_problems(region.get("xywh", []), width, height):
            findings.append(
                Finding(TECHNICAL, "REGION_BOUNDS", f"Region {region['id']}: {problem}")
            )
    return findings


def check_image_dimensions(
    record: dict, image_size: tuple[int, int], image_info: dict
) -> list[Finding]:
    declared = (record["source"]["image_width"], record["source"]["image_height"])
    info = (image_info["width"], image_info["height"])
    if declared == info == tuple(image_size):
        return []
    return [
        Finding(
            TECHNICAL,
            "IMAGE_SIZE_MISMATCH",
            f"Bildgröße widersprüchlich: Datensatz {declared}, IIIF-Antwort {info}, Bilddatei {tuple(image_size)}.",
        )
    ]


def check_ocr_file(record: dict, ocr_data: dict) -> list[Finding]:
    stored = record["ocr_result"]
    if (
        stored["raw_text"] == ocr_data["raw_text"]
        and stored["region_id"] == ocr_data["region_id"]
    ):
        return []
    return [
        Finding(
            TECHNICAL,
            "OCR_MISMATCH",
            "Die OCR-Ausgabe im Datensatz weicht von der OCR-Ergebnisdatei ab.",
        )
    ]


def check_source_integrity(
    manifest: dict, file_hashes: dict[str, str]
) -> list[Finding]:
    return [
        Finding(
            TECHNICAL,
            "SOURCE_CHECKSUM",
            f"Prüfsumme stimmt nicht mit MANIFEST überein: {entry['file']}",
        )
        for entry in manifest["files"]
        if file_hashes.get(entry["file"]) != entry["sha256"]
    ]


def check_working_basis(working: dict, current_source_hash: str) -> list[Finding]:
    if working["based_on"]["sha256"] == current_source_hash:
        return []
    return [
        Finding(
            TECHNICAL,
            "SOURCE_CHANGED",
            "Die Quelldatei wurde seit Anlage der Arbeitskopie verändert.",
        )
    ]


def check_open_reviews(record: dict) -> list[Finding]:
    findings = []
    if not record.get("final_approval"):
        findings.append(
            Finding(
                REVIEW, "RECORD_FINAL_REVIEW", "Objekt insgesamt: Endbestätigung offen."
            )
        )
    for item in record.get("review_items", []):
        findings.append(Finding(REVIEW, item["code"], item["note_de"]))
    if message := review.classification_message(record):
        findings.append(Finding(REVIEW, review.CLASSIFICATION, message))
    if record["image_description"]["review_status"] != review.DESCRIPTION_REVIEWED:
        findings.append(
            Finding(
                REVIEW,
                "DESCRIPTION_NOT_REVIEWED",
                "Bildbeschreibung: noch nicht am Bild bestätigt.",
            )
        )
    for region in record["region_annotations"]:
        if region["review_status"] != review.REGION_REVIEWED:
            findings.append(
                Finding(
                    REVIEW,
                    "REGION_NOT_REVIEWED",
                    f"Region „{region['label_de']}“: Grenzen noch nicht visuell bestätigt.",
                )
            )
        if (
            "keywords_de" in region
            and region.get("keyword_review_status") != review.KEYWORDS_ACCEPTED
        ):
            findings.append(
                Finding(
                    REVIEW,
                    "KEYWORDS_NOT_REVIEWED",
                    f"Suchbegriffe der Region „{region['label_de']}“ noch nicht bestätigt "
                    f"({review.status_label(region.get('keyword_review_status'))}).",
                )
            )
    for region in record["region_annotations"]:
        field = region.get("transcription_field")
        if (
            field
            and record["transcription"]["review_status_by_field"][field]
            != review.TRANSCRIPTION_REVIEWED
        ):
            findings.append(
                Finding(
                    REVIEW,
                    "TRANSCRIPTION_PROVISIONAL",
                    f"Transkription „{region['label_de']}“ ist vorläufig und nicht bestätigt.",
                )
            )
    return findings


def not_run_checks(record: dict) -> list[Finding]:
    findings = [
        Finding(
            NOT_RUN,
            "XSD_VALIDATION",
            "XSD-Validierung der METS/MODS-Antwort: nicht ausgeführt (geprüft sind XML-Parsing und Inhalt).",
        ),
        Finding(
            NOT_RUN,
            "LIVE_SOURCE",
            "Abgleich mit den Live-Diensten (IIIF, OAI-PMH): nicht ausgeführt; die Kerndemo nutzt nur gespeicherte Dateien.",
        ),
        Finding(
            NOT_RUN,
            "GND_LINKING",
            "Verknüpfung der Suchbegriffe mit der GND: nicht ausgeführt; Begriffe sind projektlokal.",
        ),
    ]
    if record.get("ocr_result") and record.get("evaluation") is None:
        findings.append(
            Finding(
                NOT_RUN,
                "OCR_EVALUATION",
                "OCR-Bewertung (CER/WER): nicht ausgeführt; es gibt keine freigegebene Referenztranskription.",
            )
        )
    return findings


def check_oai_source(record: dict, oai_path) -> list[Finding]:
    """Gespeicherte OAI-Antwort: Parsing und Bezug als technische, MODS-Abweichungen als fachliche Befunde."""
    try:
        root = oai.parse_shared(oai_path)
    except ET.ParseError as error:
        return [
            Finding(
                TECHNICAL, "OAI_PARSE", f"OAI-Antwort ist kein gültiges XML: {error}"
            )
        ]
    findings = [
        Finding(TECHNICAL, "OAI_CHECK", f"OAI-Prüfung nicht bestanden: {label}")
        for label, ok in oai.content_checks(root, record)
        if not ok
    ]
    try:
        _, mods = oai.book_mods(root)
    except oai.MissingMetadata:
        return findings
    rows = oai.mapping_rows(mods)
    return findings + [
        Finding(
            REVIEW,
            "MODS_DIFFERENCE",
            f"{c['label_de']}: lokal „{c['local']}“, im MODS {c['source'] or 'kein Wert'} ({c['outcome']}).",
        )
        for c in oai.compare(record, rows)
        if c["outcome"] not in oai.CONSISTENT
    ]


def unknown_optional_fields(record: dict) -> list[str]:
    return [
        label
        for path, label in OPTIONAL_UNKNOWN_FIELDS
        if get_path(record, path) is None
    ]


def run_all(
    working: dict, src: store.ObjectSource, collection: list[dict] | None = None
) -> list[Finding]:
    """Alle Prüfungen gegen die gespeicherten Quelldateien, ohne Netzabruf.

    collection: alle Datensätze der Sammlung für die ID-Prüfung; sonst nur dieser Datensatz.
    """
    record = working["record"]
    manifest = store.read_json(src.manifest)
    file_hashes = {
        e["file"]: store.sha256(src.manifest.parent / e["file"])
        for e in manifest["files"]
        if (src.manifest.parent / e["file"]).exists()
    }
    with Image.open(src.page_image) as image:
        image_size = image.size
    ocr_findings = []
    if record.get("ocr_result"):
        ocr_data = store.read_json(
            src.record.parent / record["ocr_result"]["result_file"]
        )
        ocr_findings = check_ocr_file(record, ocr_data)
    return apply_decisions(
        record,
        check_source_integrity(manifest, file_hashes)
        + check_working_basis(working, store.sha256(src.record))
        + check_required(record)
        + check_duplicate_ids(collection or [record])
        + check_image_dimensions(record, image_size, store.read_json(src.image_info))
        + check_regions(record)
        + ocr_findings
        + check_oai_source(record, src.oai_record)
        + check_open_reviews(record)
        + not_run_checks(record),
    )


def decidable(record: dict, finding: Finding) -> bool:
    """Belegte Unterschiede, die eine Person begründet entscheiden darf; keine Pflichtprüfungen."""
    codes = {review.CLASSIFICATION, "MODS_DIFFERENCE"} | {
        item["code"] for item in record.get("review_items", [])
    }
    return finding.category in {REVIEW, DOCUMENTED} and finding.code in codes


def apply_decisions(record: dict, findings: list[Finding]) -> list[Finding]:
    return [
        Finding(DOCUMENTED, f.code, f.message_de)
        if decidable(record, f)
        and review.resolves(review.decision(record, f.code, f.message_de))
        else f
        for f in findings
    ]


def approval_blockers(findings: list[Finding]) -> list[Finding]:
    return [
        f
        for f in findings
        if f.category in {TECHNICAL, REVIEW} and f.code != "RECORD_FINAL_REVIEW"
    ]
