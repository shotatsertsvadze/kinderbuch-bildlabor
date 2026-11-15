"""PAGE-XML je Objekt, nur eine Darstellung des Datensatzes. Unbestätigte Texte sind als Entwurf gekennzeichnet."""

import xml.etree.ElementTree as ET

from kinderbuch_bildlabor import annotations, review

NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"


def _points(xywh: list[int]) -> str:
    x, y, w, h = xywh
    return f"{x},{y} {x + w},{y} {x + w},{y + h} {x},{y + h}"


def page_xml(record: dict, exported_at: str) -> str:
    ET.register_namespace("", NS)
    width, height = record["source"]["image_width"], record["source"]["image_height"]
    root = ET.Element(f"{{{NS}}}PcGts")
    meta = ET.SubElement(root, f"{{{NS}}}Metadata")
    ET.SubElement(meta, f"{{{NS}}}Creator").text = "Kinderbuch-Bildlabor"
    ET.SubElement(meta, f"{{{NS}}}Created").text = exported_at
    ET.SubElement(meta, f"{{{NS}}}LastChange").text = exported_at
    ET.SubElement(
        meta, f"{{{NS}}}Comment"
    ).text = 'Endbestätigung ist keine Ground Truth; Texte mit custom="status:draft" sind ungeprüfte Entwürfe.'
    page = ET.SubElement(
        root,
        f"{{{NS}}}Page",
        imageFilename=annotations.image_reference(record),
        imageWidth=str(width),
        imageHeight=str(height),
    )
    transcription = record.get("transcription") or {}
    for region in record["region_annotations"]:
        field = region.get("transcription_field")
        if not field:
            continue
        element = ET.SubElement(
            page, f"{{{NS}}}TextRegion", id=region["id"], type="paragraph"
        )
        ET.SubElement(element, f"{{{NS}}}Coords", points=_points(region["xywh"]))
        status = transcription["review_status_by_field"][field]
        state = "confirmed" if status in review.DONE_STATUSES else "draft"
        equiv = ET.SubElement(element, f"{{{NS}}}TextEquiv", custom=f"status:{state}")
        ET.SubElement(equiv, f"{{{NS}}}Unicode").text = transcription[field]
    ET.indent(root)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + ET.tostring(root, encoding="unicode")
        + "\n"
    )
