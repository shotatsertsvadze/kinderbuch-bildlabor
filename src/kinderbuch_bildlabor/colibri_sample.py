"""Reproduzierbare Stichprobe von Colibri-Zeilen mit abweichender Klasse. Nur Lesen."""

import csv
import random
import re
from pathlib import Path

from kinderbuch_bildlabor.colibri import AUTOMATIC, MANUAL, NO_MANUAL

SEED = 20261115
FILE_PATTERN = re.compile(r"(PPN\d+)/(\d{8})_\d+\.\w+")
IIIF_URL = (
    "https://content.staatsbibliothek-berlin.de/dc/{ppn}-{scan}/full/full/0/default.jpg"
)


def scan_url(row: dict[str, str]) -> str | None:
    """Leitet die Scan-URL aus einem Dateipfad in der Zeile ab; sonst None."""
    for value in row.values():
        match = FILE_PATTERN.search(value or "")
        if match:
            return IIIF_URL.format(ppn=match[1], scan=match[2])
    return None


def sample_disagreements(
    path: Path, per_pair: int = 3, seed: int = SEED
) -> list[dict[str, str]]:
    """Je Klassenpaar (manuell, automatisch) bis zu per_pair Zeilen, gleiche Eingabe gleiche Auswahl."""
    seen: dict[tuple[str, str], int] = {}
    chosen: dict[tuple[str, str], list[dict[str, str]]] = {}
    rng = random.Random(seed)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in (MANUAL, AUTOMATIC) if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(
                "In der Colibri-Datei fehlen die Spalten: " + ", ".join(missing)
            )
        for row in reader:
            manual = (row[MANUAL] or "").strip()
            automatic = (row[AUTOMATIC] or "").strip()
            if manual in ("", NO_MANUAL) or manual == automatic:
                continue
            pair = (manual, automatic)
            seen[pair] = seen.get(pair, 0) + 1
            bucket = chosen.setdefault(pair, [])
            if len(bucket) < per_pair:
                bucket.append(row)
            else:
                slot = rng.randrange(seen[pair])
                if slot < per_pair:
                    bucket[slot] = row
    return [row for pair in sorted(chosen) for row in chosen[pair]]
