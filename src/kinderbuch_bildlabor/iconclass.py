"""Iconclass-Vorschläge aus einer kleinen CC0-Auswahl. Reine Berechnung, nichts wird gespeichert."""

import json
from dataclasses import dataclass
from functools import cache

from kinderbuch_bildlabor.store import ROOT

PATH = ROOT / "sammlung" / "iconclass_auswahl.json"


@dataclass(frozen=True)
class Suggestion:
    notation: str
    label_de: str

    @property
    def line(self) -> str:
        return f"Iconclass {self.notation} {self.label_de}"


@cache
def entries() -> list[dict]:
    return json.loads(PATH.read_text(encoding="utf-8"))["eintraege"]


def suggest(text: str) -> list[Suggestion]:
    """Treffer in der Reihenfolge der Auswahldatei; Suchwörter als Teilstring, ohne Großschreibung."""
    lowered = text.lower()
    return [
        Suggestion(entry["notation"], entry["label_de"])
        for entry in entries()
        if any(word in lowered for word in entry["woerter"])
    ]
