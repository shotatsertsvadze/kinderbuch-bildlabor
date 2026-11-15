"""Übereinstimmung von Erst- und Zweitprüfung über die Sammlung. Konventionsstatistik, keine Ground Truth."""

from collections import Counter

from kinderbuch_bildlabor import review, second_review


def kappa(a: list[bool], b: list[bool]) -> float | None:
    """Cohens Kappa; None, wenn eine Reihe konstant ist (dann trennt es nichts)."""
    n = len(a)
    if n == 0 or n != len(b) or len(set(a)) < 2 or len(set(b)) < 2:
        return None
    observed = sum(x == y for x, y in zip(a, b)) / n
    chance = sum((a.count(v) / n) * (b.count(v) / n) for v in (True, False))
    return (observed - chance) / (1 - chance)


def collect(records: dict[str, dict]) -> dict:
    """Je Prüfbereich Zustimmung/Abweichung (nur gültige Einträge) und strittige Objekte."""
    per_area: dict[str, Counter] = {}
    disputed: list[str] = []
    for object_id, record in records.items():
        if second_review.summary(record) is None:
            continue
        for area in review.review_areas(record):
            key = second_review.area_key(area)
            state = second_review.entry_state(record, key)
            if state not in (second_review.AGREE, second_review.DISAGREE):
                continue
            per_area.setdefault(key, Counter())[state] += 1
            if state == second_review.DISAGREE and object_id not in disputed:
                disputed.append(object_id)
    # Die Endbestätigung gilt je Bereich als Zustimmung der ersten Person.
    first: list[bool] = []
    second: list[bool] = []
    for counts in per_area.values():
        first += [True] * sum(counts.values())
        second += [True] * counts["agree"] + [False] * counts["disagree"]
    return {"per_area": per_area, "disputed": disputed, "kappa": kappa(first, second)}
