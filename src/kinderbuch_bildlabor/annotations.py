"""W3C Web Annotation (AnnotationPage) je Objekt, nur eine Darstellung des Datensatzes.

Die Bildbeschreibung hängt nur an der ersten Illustrationsregion. Jede Region wird eine Annotation mit Bereichsangabe (FragmentSelector xywh) am IIIF-Bild.
Unbestätigte Inhalte stehen als Entwurf (bl:status) darin, nie als bestätigt.
"""

from kinderbuch_bildlabor import review

BL = "urn:bildlabor:vocab#"
CONTEXT = ["http://www.w3.org/ns/anno.jsonld", {"bl": BL}]
NOTE = (
    "Endbestätigung ist keine Ground Truth; Inhalte mit bl:status 'draft' sind "
    "ungeprüfte Entwürfe."
)


def _body(record: dict, value: str, purpose: str, status: str, log_area: str) -> dict:
    confirmed = status in review.DONE_STATUSES
    entry = review.last_confirmation(record, log_area) if confirmed else None
    body = {
        "type": "TextualBody",
        "value": value,
        "language": "de",
        "purpose": purpose,
        "bl:status": "confirmed" if confirmed else "draft",
        "bl:review_status": status,
        "bl:confirmed_by": entry and entry["by"],
        "bl:confirmed_at": entry and entry["at"],
        "bl:note": NOTE,
    }
    return body


def _bodies(record: dict, region: dict, describe: bool) -> list[dict]:
    bodies = []
    if describe:
        desc = record["image_description"]
        bodies.append(
            _body(
                record,
                desc["working_description_de"],
                "describing",
                desc["review_status"],
                "image_description",
            )
        )
    if region.get("keywords_de"):
        bodies.append(
            _body(
                record,
                "; ".join(region["keywords_de"]),
                "tagging",
                region["keyword_review_status"],
                f"{region['id']}/keywords_de",
            )
        )
    if field := region.get("transcription_field"):
        transcription = record["transcription"]
        bodies.append(
            _body(
                record,
                transcription[field],
                "supplementing",
                transcription["review_status_by_field"][field],
                f"transcription/{field}",
            )
        )
    return bodies


def annotation_page(record: dict, exported_at: str) -> dict:
    source = record["source"]
    canvas = source["image_info_url"].removesuffix("/info.json")
    items = []
    first_illustration = next(
        (
            r["id"]
            for r in record["region_annotations"]
            if r["region_type"] == "illustration"
        ),
        None,
    )
    for region in record["region_annotations"]:
        x, y, w, h = region["xywh"]
        confirmed = region["review_status"] in review.DONE_STATUSES
        entry = review.last_confirmation(record, region["id"]) if confirmed else None
        items.append(
            {
                "id": f"urn:bildlabor:{region['id']}",
                "type": "Annotation",
                # Mirador 3.4 zeigt nur Annotationen mit Motivation "commenting" an
                "motivation": ["describing", "commenting"],
                "label": region["label_de"],
                "bl:status": "confirmed" if confirmed else "draft",
                "bl:region_review_status": region["review_status"],
                "bl:region_confirmed_by": entry and entry["by"],
                "bl:region_confirmed_at": entry and entry["at"],
                "body": _bodies(record, region, region["id"] == first_illustration),
                "target": {
                    "type": "SpecificResource",
                    "source": canvas,
                    "selector": {
                        "type": "FragmentSelector",
                        "conformsTo": "http://www.w3.org/TR/media-frags/",
                        "value": f"xywh={x},{y},{w},{h}",
                    },
                },
            }
        )
    return {
        "@context": CONTEXT,
        "id": f"urn:bildlabor:{record['id']}:annotations",
        "type": "AnnotationPage",
        "bl:exported_at": exported_at,
        "bl:object_status": record["status"],
        "bl:note": NOTE,
        "items": items,
    }
