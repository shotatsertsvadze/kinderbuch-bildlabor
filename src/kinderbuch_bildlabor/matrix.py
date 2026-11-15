"""Kreuztabelle manuelle x automatische Klasse. Reine Berechnung, nichts wird gespeichert."""

from kinderbuch_bildlabor import ui


def cells(
    collection: list[ui.Current],
) -> tuple[dict[tuple[str, str], list[str]], list[str]]:
    """Objekt-IDs je (manuell, automatisch); Objekte ohne beide Klassen gesondert."""
    table: dict[tuple[str, str], list[str]] = {}
    missing: list[str] = []
    for cur in collection:
        source = cur.record["source"]
        manual = source.get("colibri_groundtruth")
        automatic = source.get("colibri_classification")
        if manual and automatic:
            table.setdefault((manual, automatic), []).append(cur.id)
        else:
            missing.append(cur.id)
    return table, missing
