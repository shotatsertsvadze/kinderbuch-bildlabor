"""Eigenständiger HTML-Prüfbericht je Objekt (Druck als PDF über den Browser). Nur Lesen."""

import base64
import io
from html import escape

from PIL import Image

from kinderbuch_bildlabor import regions, second_review, timeline, workflow

FRESHNESS = {
    "none": "kein Export vorhanden",
    "current": "Export aktuell",
    "stale": "Export veraltet (seitdem gespeichert)",
    "foreign": "Export stammt aus fremder Änderungsgeschichte",
    "damaged": "Export beschädigt",
}
NOTE = "Keine Ground Truth: Endbestätigung und Zweitprüfung sind Konventionen nach selbst angegebenen Namen."


def _data_uri(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def _table(head: list[str], rows: list[list[str]]) -> str:
    cells = "".join(f"<th>{escape(h)}</th>" for h in head)
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>"
        for row in rows
    )
    return f"<table><tr>{cells}</tr>{body}</table>"


def build(record: dict, page: Image.Image, export_state: str) -> str:
    title = record["bibliographic_metadata_from_colibri"]["title"]
    parts = [f"<h1>{escape(title)}</h1>", f"<p><strong>{escape(NOTE)}</strong></p>"]
    parts.append(
        f"<p>Status: {escape(record['status'])}; {escape(FRESHNESS.get(export_state, export_state))}</p>"
    )
    approval = record.get("final_approval")
    if approval:
        parts.append(
            f"<p>Endbestätigung: {escape(approval['by'])}, {escape(approval['at'])}</p>"
        )
    rows = []
    for region in record["region_annotations"]:
        crop = regions.crop(page, region["xywh"])
        crop.thumbnail((400, 300))
        parts.append(
            f'<figure><img src="{_data_uri(crop)}" alt="Ausschnitt {escape(region["id"])}">'
            f"<figcaption>{escape(region['label_de'])}</figcaption></figure>"
        )
        rows.append(
            [
                region["id"],
                region["region_type"],
                region["xywh"],
                region["review_status"],
            ]
        )
    parts.append(
        "<h2>Regionen</h2>" + _table(["Region", "Typ", "xywh", "Status"], rows)
    )
    parts.append(
        "<h2>Beschreibung (Arbeitstext)</h2><p>"
        + escape(record["image_description"]["working_description_de"])
        + "</p>"
    )
    decisions = [
        [d["outcome_de"], d["rationale_de"], d.get("by", ""), d.get("at", "")]
        for d in record.get("decisions", {}).values()
    ]
    parts.append(
        "<h2>Entscheidungen zu Hinweisen</h2>"
        + _table(["Ergebnis", "Begründung", "Person", "Zeit"], decisions)
    )
    second = []
    if workflow.approved(record):
        for key, entry in record.get("second_review", {}).items():
            second.append(
                [
                    key,
                    second_review.entry_state(record, key),
                    entry["by"],
                    entry.get("reason") or "",
                ]
            )
    parts.append(
        "<h2>Zweitprüfung</h2>"
        + _table(["Bereich", "Stand", "Person", "Grund"], second)
    )
    parts.append(
        "<h2>Verlauf</h2>"
        + _table(
            ["Zeit", "Art", "Person", "Bereich", "Vorgang"],
            [
                [e["at"], e["kind"], e["person"], e["area"], e["text"]]
                for e in timeline.events(record)
            ],
        )
    )
    style = "body{font-family:sans-serif;max-width:900px;margin:2em auto}table{border-collapse:collapse}td,th{border:1px solid #888;padding:4px}"
    return (
        '<!doctype html><html lang="de"><head><meta charset="utf-8">'
        f"<title>{escape(title)}</title><style>{style}</style></head><body>"
        + "".join(parts)
        + "</body></html>"
    )
