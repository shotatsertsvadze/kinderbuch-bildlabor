"""Warteschlange: welches Objekt zuerst geprüft werden sollte. Reine Berechnung, nichts wird gespeichert."""

from dataclasses import dataclass

from kinderbuch_bildlabor import review, ui, validate, workflow


@dataclass(frozen=True)
class Row:
    id: str
    title: str
    disagreement: bool
    blockers: int
    confirmed: int
    total: int
    approved: bool


def order(rows: list[Row]) -> list[Row]:
    """Endbestätigte zuletzt; sonst offene Klassenabweichung, mehr Blocker, weniger bestätigte Bereiche zuerst."""
    return sorted(
        rows, key=lambda r: (r.approved, not r.disagreement, -r.blockers, r.confirmed)
    )


def row(cur: ui.Current, records: list[dict]) -> Row:
    record = cur.record
    message = review.classification_message(record)
    areas = review.review_areas(record)
    findings = validate.run_all(cur.working, cur.src, records)
    return Row(
        id=cur.id,
        title=record["bibliographic_metadata_from_colibri"]["title"],
        disagreement=message is not None
        and review.classification_status(record, message)
        != review.CLASSIFICATION_DECIDED,
        blockers=len(validate.approval_blockers(findings)),
        confirmed=workflow.area_counts(areas)[0],
        total=len(areas),
        approved=workflow.approved(record),
    )


def rank(collection: list[ui.Current]) -> list[Row]:
    records = [cur.record for cur in collection]
    return order([row(cur, records) for cur in collection])
