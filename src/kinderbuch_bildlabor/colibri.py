"""Auszählung der ganzen Colibri-CSV (manuelle x automatische Klasse). Nur Lesen, nichts wird gespeichert."""

import csv
import hashlib
import io
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

MANUAL = "groundtruth"
AUTOMATIC = "classification"
NO_MANUAL = "-0"
MANIFEST_SHA256 = "9f8373e7107ad4ed698903bd5a9044fe7c2e169ac7557e15ccac384a9be0493f"


@dataclass(frozen=True)
class Aggregate:
    cells: dict[tuple[str, str], int]
    rows: int
    without_manual: int
    sha256: str


class _Hashing(io.RawIOBase):
    """Reicht Bytes durch und hasht sie im selben Durchlauf."""

    def __init__(self, raw) -> None:
        self.raw = raw
        self.digest = hashlib.sha256()

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        count = self.raw.readinto(buffer)
        self.digest.update(memoryview(buffer)[:count])
        return count


def aggregate(path: Path) -> Aggregate:
    cells: Counter[tuple[str, str]] = Counter()
    rows = without_manual = 0
    with path.open("rb") as raw:
        source = _Hashing(raw)
        text = io.TextIOWrapper(
            io.BufferedReader(source), encoding="utf-8-sig", newline=""
        )
        reader = csv.DictReader(text)
        missing = [c for c in (MANUAL, AUTOMATIC) if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(
                "In der Colibri-Datei fehlen die Spalten: " + ", ".join(missing)
            )
        for row in reader:
            rows += 1
            manual = (row[MANUAL] or "").strip()
            if manual in ("", NO_MANUAL):
                without_manual += 1
            else:
                cells[(manual, (row[AUTOMATIC] or "").strip())] += 1
        for _ in iter(lambda: source.read(1 << 20), b""):
            pass
    return Aggregate(dict(cells), rows, without_manual, source.digest.hexdigest())
