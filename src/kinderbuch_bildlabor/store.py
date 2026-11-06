"""Lesen der unveränderten Quelldateien und Speichern der lokalen Arbeitskopie.

Die Quelldateien werden nie geschrieben. Alle Bearbeitungen landen je Objekt in einer
Arbeitskopie, die auf Datei und Prüfsumme der Quelle verweist. Welche Quelldateien zu
einem Objekt gehören, steht im Katalog sammlung/katalog.json.
"""

import hashlib
import json
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "Kinderbuch_Bildlabor_Start"
# Getrennter Datenordner für Tests, damit echte Bearbeitungen unberührt bleiben
DATA_DIR = Path(os.environ.get("BILDLABOR_DATA_DIR", ROOT))
WORK_DIR = DATA_DIR / "data" / "work"
EXPORT_DIR = DATA_DIR / "exports"

CATALOG = ROOT / "sammlung" / "katalog.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class ObjectSource:
    """Unveränderliche Quelldateien eines Objekts (Pfade relativ zum Projekt im Katalog)."""
    id: str
    record: Path
    page_image: Path
    image_info: Path
    oai_record: Path
    manifest: Path


def catalog() -> list[ObjectSource]:
    return [ObjectSource(entry["id"], *(ROOT / entry[key] for key in
                                        ("record", "page_image", "image_info", "oai_record", "manifest")))
            for entry in read_json(CATALOG)["objects"]]


def object_source(object_id: str) -> ObjectSource:
    return next(src for src in catalog() if src.id == object_id)


def write_json(path: Path, data) -> None:
    """Schreibt über eine temporäre Datei, damit kein halb geschriebener Stand entsteht."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Eigener Name je Schreibvorgang: gleichzeitige Speicherungen dürfen sich nicht die Datei teilen
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as tmp:
        tmp.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    Path(tmp.name).replace(path)


# Alle Browser-Sitzungen laufen als Threads in einem Streamlit-Prozess; die Sperre macht
# Laden, Ändern und Speichern zu einem Schritt. Mehrere Server-Prozesse schützt sie nicht.
LOCK = threading.RLock()

MIGRATION_SPLIT_TRANSCRIPTION = "Modellumstellung: Prüfstand der Transkription je Feld"
MIGRATION_DESCRIPTION_STATUS = "Modellumstellung: eigener Prüfstand der Beschreibung"


def split_transcription_status(record: dict) -> bool:
    """Älteres Format: der gemeinsame Transkriptions-Prüfstand gilt danach für jedes Feld einzeln."""
    transcription = record.get("transcription")
    if not transcription or "review_status" not in transcription:
        return False
    status = transcription.pop("review_status")
    fields = [r["transcription_field"] for r in record["region_annotations"] if r.get("transcription_field")]
    transcription["review_status_by_field"] = {field: status for field in fields}
    return True


def add_description_status(record: dict) -> bool:
    """Ältere Datensätze hatten keinen Prüfstand der Beschreibung; bestätigt wurde sie nie."""
    description = record["image_description"]
    if "review_status" in description:
        return False
    description["review_status"] = "unreviewed"
    return True


MIGRATIONS = [(split_transcription_status, MIGRATION_SPLIT_TRANSCRIPTION),
              (add_description_status, MIGRATION_DESCRIPTION_STATUS)]


def migrate_record(record: dict) -> list[str]:
    """Wendet alle offenen Umstellungen an; liefert ihre Bezeichnungen."""
    return [label for migrate, label in MIGRATIONS if migrate(record)]


def new_working_copy(src: ObjectSource) -> dict:
    record = read_json(src.record)
    migrate_record(record)
    return {
        "based_on": {
            "file": src.record.relative_to(ROOT).as_posix(),
            "sha256": sha256(src.record),
        },
        "change_log": [],
        "record": record,
    }


def work_path(record_id: str, work_dir: Path | None = None) -> Path:
    return (work_dir or WORK_DIR) / f"{record_id}.json"


def load_working_copy(src: ObjectSource, work_dir: Path | None = None) -> dict:
    """Lädt die gespeicherte Arbeitskopie oder legt eine neue aus der Quelle an (ungespeichert)."""
    path = work_path(src.id, work_dir)
    with LOCK:
        if not path.exists():
            return new_working_copy(src)
        working = read_json(path)
        # Einmalige, protokollierte Umstellung gespeicherter Stände im älteren Format
        for label in migrate_record(working["record"]):
            save_working_copy(working, label, work_dir)
        return working


def save_working_copy(working: dict, area_de: str, work_dir: Path | None = None) -> Path:
    working["change_log"].append({"saved_at": now_utc(), "area_de": area_de})
    path = work_path(working["record"]["id"], work_dir)
    with LOCK:
        write_json(path, working)
    return path


def update_working_copy(src: ObjectSource, change, area_de: str, work_dir: Path | None = None) -> bool:
    """Lädt den gespeicherten Stand, wendet change(record) an und speichert nur echte Änderungen."""
    with LOCK:
        working = load_working_copy(src, work_dir)
        if not change(working["record"]):
            return False
        save_working_copy(working, area_de, work_dir)
        return True
