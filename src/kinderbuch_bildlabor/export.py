"""Export als JSON (vollständig) und CSV (Übersicht je Region) sowie Rückladeprüfung.

Herkunft, Rechte und Namensnennung stehen in jeder CSV-Zeile, damit sie beim
Weitergeben einzelner Zeilen nicht verloren gehen. Leere CSV-Zellen bedeuten "unbekannt".
"""

import csv
import io
from pathlib import Path

from kinderbuch_bildlabor import store

CSV_COLUMNS = [
    "objekt_id",
    "objekt_status",
    "endpruefung_person",
    "endpruefung_am",
    "ppn",
    "titel",
    "physische_seite",
    "scan_nummer",
    "seitenbezeichnung_mets",
    "gedruckte_seitenzahl",
    "region_id",
    "bezeichnung",
    "regionstyp",
    "x",
    "y",
    "breite",
    "hoehe",
    "koordinatenbezug",
    "regionen_pruefstatus",
    "regionen_herkunft",
    "beschreibung",
    "beschreibung_pruefstatus",
    "beschreibung_herkunft",
    "suchbegriffe",
    "suchbegriffe_vokabular",
    "suchbegriffe_pruefstatus",
    "suchbegriffe_herkunft",
    "transkription",
    "transkription_pruefstatus",
    "illustrator",
    "quelle_institution",
    "quelle_ansicht",
    "quelle_bildinfo",
    "rechte_quellwerk",
    "colibri_datei",
    "colibri_lizenz",
    "colibri_namensnennung",
    "exportiert_am",
]


def export_json(working: dict, path: Path) -> dict:
    data = {
        "exported_at": store.now_utc(),
        "based_on": working["based_on"],
        "change_log": working["change_log"],
        "record": working["record"],
    }
    store.write_json(path, data)
    return data


def csv_rows(record: dict, exported_at: str) -> list[dict]:
    source = record["source"]
    biblio = record["bibliographic_metadata_from_colibri"]
    transcription = record.get("transcription") or {}
    description = record["image_description"]
    rows = []
    for region in record["region_annotations"]:
        x, y, w, h = region["xywh"]
        field = region.get("transcription_field")
        rows.append(
            {
                "objekt_id": record["id"],
                "objekt_status": record["status"],
                "endpruefung_person": record.get("final_approval", {}).get("by"),
                "endpruefung_am": record.get("final_approval", {}).get("at"),
                "ppn": source["ppn"],
                "titel": biblio["title"],
                "physische_seite": source["physical_page_id"],
                "scan_nummer": source["scan_number"],
                "seitenbezeichnung_mets": source.get("page_label_mets"),
                "gedruckte_seitenzahl": source["printed_page_number"],
                "region_id": region["id"],
                "bezeichnung": region["label_de"],
                "regionstyp": region["region_type"],
                "x": x,
                "y": y,
                "breite": w,
                "hoehe": h,
                "koordinatenbezug": f"Pixel im Ausgangsbild {source['image_width']} × {source['image_height']}",
                "regionen_pruefstatus": region["review_status"],
                "regionen_herkunft": region.get("region_origin_de"),
                # Die Beschreibung gilt dem ganzen Bild und steht deshalb nur in der Zeile der Illustration
                "beschreibung": description["working_description_de"]
                if region["region_type"] == "illustration"
                else None,
                "beschreibung_pruefstatus": description["review_status"]
                if region["region_type"] == "illustration"
                else None,
                "beschreibung_herkunft": description.get("description_origin_de")
                if region["region_type"] == "illustration"
                else None,
                "suchbegriffe": "; ".join(region.get("keywords_de", [])),
                "suchbegriffe_vokabular": region.get("keyword_vocabulary"),
                "suchbegriffe_pruefstatus": region.get("keyword_review_status"),
                "suchbegriffe_herkunft": region.get("keyword_origin_de"),
                "transkription": transcription[field] if field else None,
                "transkription_pruefstatus": transcription["review_status_by_field"][
                    field
                ]
                if field
                else None,
                "illustrator": record["image_description"]["illustrator"],
                "quelle_institution": source["institution"],
                "quelle_ansicht": source["viewer_url"],
                "quelle_bildinfo": source["image_info_url"],
                "rechte_quellwerk": biblio["rights_statement"],
                "colibri_datei": source["colibri_file_reference"],
                "colibri_lizenz": source["colibri_dataset_license"],
                "colibri_namensnennung": source["colibri_dataset_credit"],
                "exportiert_am": exported_at,
            }
        )
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    """utf-8-sig, damit Excel Umlaute und typografische Anführungszeichen korrekt öffnet."""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    # Nur die CSV-Darstellung entschärfen; Originaltexte bleiben unverändert.
    writer.writerows(
        {
            key: "'" + value
            if isinstance(value, str)
            and (
                value.startswith(("\t", "\r", "\n"))
                or value.lstrip().startswith(("=", "+", "-", "@"))
            )
            else value
            for key, value in row.items()
        }
        for row in rows
    )
    store.write_text(path, buffer.getvalue(), encoding="utf-8-sig", newline="")


def export_csv(record: dict, exported_at: str, path: Path) -> None:
    write_csv(csv_rows(record, exported_at), path)


def export_collection_csv(records: list[dict], exported_at: str, path: Path) -> None:
    """Eine Übersicht aller Objekte der Sammlung, eine Zeile je Region."""
    write_csv(
        [row for record in records for row in csv_rows(record, exported_at)], path
    )


def leaves(data, path=()):
    """Alle Endwerte eines verschachtelten JSON-Objekts mit ihrem Pfad."""
    if isinstance(data, dict):
        for key, value in data.items():
            yield from leaves(value, path + (key,))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            yield from leaves(value, path + (index,))
    else:
        yield path, data


def differing_fields(original: dict, reloaded: dict) -> list[str]:
    """Pfade aller Endwerte, die fehlen, hinzukommen oder sich unterscheiden."""
    before, after = dict(leaves(original)), dict(leaves(reloaded))
    paths = sorted(
        (
            p
            for p in before.keys() | after.keys()
            if before.get(p, ...) != after.get(p, ...)
        ),
        key=str,
    )
    return [" › ".join(str(part) for part in path) for path in paths]


def later_changes(working: dict, exported: dict) -> list[dict] | None:
    """Nach dem Export gespeicherte Änderungen der Arbeitskopie.

    Leer: Export ist aktuell. None: Export stammt nicht aus dieser Änderungsgeschichte.
    """
    count = len(exported["change_log"])
    if working["change_log"][:count] != exported["change_log"]:
        return None
    return working["change_log"][count:]


def roundtrip_report(original: dict, reloaded: dict) -> list[tuple[str, bool]]:
    """Vergleicht den bearbeiteten Datensatz mit dem erneut geladenen Export.

    Nur aussagekräftig, wenn der Export aktuell ist (later_changes leer).
    """
    before, after = dict(leaves(original)), dict(leaves(reloaded))

    def same(selector) -> bool:
        return {p: v for p, v in before.items() if selector(p, v)} == {
            p: v for p, v in after.items() if selector(p, v)
        }

    # Nur Texte an Pfaden, die in beiden Ständen existieren; fehlende oder
    # hinzugekommene Felder sind keine Unicode-Frage und fallen im Gesamtvergleich auf
    unicode_kept = all(
        after[p] == v
        for p, v in before.items()
        if p in after and isinstance(v, str) and not v.isascii()
    )
    return [
        ("Unicode-Texte unverändert (z. B. ‘ „ ä ß ×)", unicode_kept),
        (
            "Nullwerte bleiben null (nicht leer, nicht entfernt)",
            same(lambda p, v: v is None),
        ),
        (
            "Regionen und Koordinaten unverändert",
            original["region_annotations"] == reloaded["region_annotations"],
        ),
        # Auch verschachtelte Prüfstände wie review_status_by_field › working_title
        (
            "Alle Prüfstände unverändert",
            same(
                lambda p, v: any(isinstance(key, str) and "status" in key for key in p)
            ),
        ),
        ("Gesamter Datensatz identisch", original == reloaded),
    ]
