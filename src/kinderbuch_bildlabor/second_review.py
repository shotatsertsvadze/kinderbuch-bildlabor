"""Zweitprüfung nach der Endbestätigung: je Prüfbereich Zustimmung oder Abweichung einer zweiten Person.

Der Name ist nur eine Konvention ohne Anmeldung. Die Zweitprüfung vergibt keine Ground Truth.
Ein Eintrag gilt nur, solange der Inhalt seines Bereichs dem geprüften entspricht (Inhaltsprüfsumme).
"""

import hashlib
import json
from typing import Any

from kinderbuch_bildlabor import review, workflow
from kinderbuch_bildlabor.store import now_utc

AGREE = "agree"
DISAGREE = "disagree"


class SecondReviewBlocked(ValueError):
    pass


def area_key(area: dict) -> str:
    return area.get("log_area") or "classification"


def content_hash(record: dict, key: str) -> str:
    if key == "classification":
        message = review.classification_message(record)
        content = [
            message,
            message and review.decision(record, review.CLASSIFICATION, message),
        ]
    elif key == "bibliographic":
        content = [
            record[section][field]
            for _, section, field in review.BIBLIO_FIELDS.values()
        ]
    elif key == "image_description":
        content = record["image_description"]["working_description_de"]
    elif key.endswith("/keywords_de"):
        content = review.find_region(record, key.removesuffix("/keywords_de"))[
            "keywords_de"
        ]
    elif key.startswith("transcription/"):
        content = record["transcription"][key.removeprefix("transcription/")]
    else:
        content = review.find_region(record, key)["xywh"]
    return hashlib.sha256(json.dumps(content, ensure_ascii=False).encode()).hexdigest()[
        :12
    ]


def entry_state(record: dict, key: str) -> str:
    """'open', 'agree', 'disagree' oder 'stale' (Inhalt geändert oder gleiche Person wie Endbestätigung)."""
    entry = record.get("second_review", {}).get(key)
    if entry is None:
        return "open"
    approver = record.get("final_approval", {}).get("by", "")
    if entry["content_hash"] != content_hash(record, key) or same_person(
        entry["by"], approver
    ):
        return "stale"
    return AGREE if entry["agrees"] else DISAGREE


def same_person(a: str, b: str) -> bool:
    return a.strip().casefold() == b.strip().casefold()


def summary(record: dict) -> dict[str, Any] | None:
    """None, solange das Objekt nicht endbestätigt ist."""
    if not workflow.approved(record):
        return None
    states = [entry_state(record, area_key(a)) for a in review.review_areas(record)]
    counts: dict[str, Any] = {
        s: states.count(s) for s in ("agree", "disagree", "open", "stale")
    }
    entries = record.get("second_review", {})
    counts["persons"] = sorted(
        {
            e["by"]
            for k, e in entries.items()
            if k in {area_key(a) for a in review.review_areas(record)}
            and entry_state(record, k) in (AGREE, DISAGREE)
        }
    )
    return counts


def summary_text(record: dict) -> str | None:
    counts = summary(record)
    if counts is None:
        return None
    return (
        f"{counts['agree']} Zustimmung, {counts['disagree']} Abweichung, "
        f"{counts['open']} offen, {counts['stale']} veraltet"
    )


def record_review(
    record: dict, key: str, by: str, agrees: bool, reason: str, seen_hash: str
) -> bool:
    if not workflow.approved(record):
        raise SecondReviewBlocked(
            "Die Zweitprüfung ist erst nach der Endbestätigung möglich."
        )
    if key not in {area_key(a) for a in review.review_areas(record)}:
        raise SecondReviewBlocked("Unbekannter Prüfbereich.")
    by, reason = by.strip(), reason.strip()
    if not by:
        raise SecondReviewBlocked("Bitte zuerst einen Namen eintragen.")
    if same_person(by, record["final_approval"]["by"]):
        raise SecondReviewBlocked(
            "Die Zweitprüfung muss von einer anderen Person als der Endbestätigung stammen."
        )
    if not agrees and not reason:
        raise SecondReviewBlocked("Eine Abweichung braucht eine Begründung.")
    current = content_hash(record, key)
    if seen_hash != current:
        raise review.ContentChanged(
            "Der Bereich wurde inzwischen geändert. Bitte den aktuellen Stand ansehen."
        )
    entry = {
        "by": by,
        "agrees": agrees,
        "reason": None if agrees else reason,
        "content_hash": current,
    }
    previous = record.setdefault("second_review", {}).get(key)
    if previous and {k: previous[k] for k in entry} == entry:
        return False
    record["second_review"][key] = {**entry, "at": now_utc()}
    review.log(
        record,
        f"second_review/{key}",
        "Zweitprüfung: " + ("Zustimmung" if agrees else f"Abweichung ({reason})"),
        by,
    )
    return True
