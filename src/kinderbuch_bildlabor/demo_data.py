"""Kuratierter Demonstrationsstand für die öffentliche Ansicht (Ordner demo/).

Übernimmt Arbeitskopien und vollständige Exportsätze aus einem eigens angelegten Bearbeitungsordner,
prüft sie streng und legt Prüfsummen, Rechte und Herkunft daneben. Erzeugt keine Prüfungen.

Aufruf:
  python -m kinderbuch_bildlabor.demo_data build ORDNER --bestaetigt-von "Vor- und Nachname"
  python -m kinderbuch_bildlabor.demo_data check [ORDNER]
"""

import argparse
import copy
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from kinderbuch_bildlabor import actions, export, store

TARGET = store.ROOT / "demo"
# Nur diese Namen dürfen in veröffentlichten Bestätigungen und Entscheidungen stehen
ALLOWED_NAMES = {"Shota Tsertsvadze"}
NAME_KEYS = {"by", "withdrawn_by"}
DOCS = ["README.md", "LICENSES.md", "PROVENANCE.md"]
MANIFEST = "MANIFEST.json"
OPEN_MARK = "OFFEN:"
ATTESTATION = "Selbst geprüft und entschieden von"


class DemoDataError(Exception):
    pass


def export_files(object_id: str) -> list[str]:
    return [
        f"{object_id}.json",
        f"{object_id}.csv",
        f"{object_id}.annotations.json",
        f"{object_id}.page.xml",
    ]


def names(data) -> set[str]:
    """Alle Personennamen in Bestätigungen, Entscheidungen und Rückzügen."""
    if isinstance(data, dict):
        found = {v for k, v in data.items() if k in NAME_KEYS and isinstance(v, str)}
        return found.union(*(names(v) for v in data.values()))
    if isinstance(data, list):
        return set().union(*(names(v) for v in data))
    return set()


def data_files(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.rglob("*")
        if p.is_file() and p.relative_to(folder).as_posix() not in [*DOCS, MANIFEST]
    )


def check_object(folder: Path, src: store.ObjectSource) -> list[str]:
    problems = []
    working = store.read_json(store.work_path(src.id, folder / "data" / "work"))
    if working["based_on"] != {
        "file": src.reference(),
        "sha256": store.sha256(src.record),
    }:
        problems.append(
            f"{src.id}: Arbeitskopie beruht nicht auf der aktuellen Quelle."
        )
    if store.migrate_record(copy.deepcopy(working["record"])):
        problems.append(f"{src.id}: Arbeitskopie im älteren Format; bitte neu anlegen.")
    json_path = folder / "exports" / f"{src.id}.json"
    if not json_path.is_file():
        return [*problems, f"{src.id}: Export fehlt."]
    exported = store.read_json(json_path)
    if export.later_changes(working, exported) != [] or (
        exported["record"] != working["record"]
    ):
        problems.append(f"{src.id}: Export entspricht nicht dem letzten Arbeitsstand.")
    if bad := actions.invalid_exports(src.id, exported, folder / "exports"):
        problems.append(
            f"{src.id}: Exportdateien passen nicht zusammen: "
            + ", ".join(p.name for p in bad)
        )
    if foreign := names(working) - ALLOWED_NAMES:
        problems.append(f"{src.id}: Nicht zugelassene Namen: {sorted(foreign)}")
    return problems


def check(folder: Path, published: bool = True) -> list[str]:
    """Leere Liste, wenn der Ordner als Demonstrationsstand veröffentlicht werden darf."""
    sources = {src.id: src for src in store.catalog() if src.profile == "fixture"}
    work = sorted((folder / "data" / "work").glob("*.json"))
    ids = [p.stem for p in work]
    allowed = {f"data/work/{i}.json" for i in ids} | {
        f"exports/{name}" for i in ids for name in export_files(i)
    }
    # Im Bearbeitungsordner liegen auch Verlauf und Zwischenspeicher; übernommen werden sie nie
    problems = [
        f"Nicht zugelassene Datei: {path}"
        for path in (p.relative_to(folder).as_posix() for p in data_files(folder))
        if published and path not in allowed
    ]
    if not ids:
        problems.append("Keine Arbeitskopie gefunden.")
    for object_id in ids:
        if object_id not in sources:
            problems.append(f"{object_id}: kein Objekt der kuratierten Sammlung.")
        else:
            problems += check_object(folder, sources[object_id])
    if published:
        problems += check_published(folder)
    return problems


def check_published(folder: Path) -> list[str]:
    problems = [f"{doc} fehlt." for doc in DOCS if not (folder / doc).is_file()]
    if (folder / "LICENSES.md").is_file() and OPEN_MARK in (
        folder / "LICENSES.md"
    ).read_text("utf-8"):
        problems.append(f"LICENSES.md enthält noch offene Angaben ({OPEN_MARK}).")
    manifest = folder / MANIFEST
    if not manifest.is_file():
        return [*problems, f"{MANIFEST} fehlt."]
    listed = store.read_json(manifest)["files"]
    actual = {
        p.relative_to(folder).as_posix(): store.sha256(p) for p in data_files(folder)
    }
    if listed != actual:
        problems.append(
            f"Prüfsummen in {MANIFEST} stimmen nicht mit den Dateien überein."
        )
    return problems


def code_version() -> str:
    try:
        return subprocess.run(
            ["git", "describe", "--always", "--dirty"],
            cwd=store.ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unbekannt"


def readme(version: str) -> str:
    return (
        "# Demonstrationsdaten der öffentlichen Ansicht\n\n"
        "Kuratierter Stand für die öffentliche, nur lesbare Demo des Kinderbuch-Bildlabors. "
        "Die Bestätigungen und Entscheidungen sind Demonstrationsprüfungen des Bewerbers: "
        "nicht unabhängig verifiziert, keine Zweitprüfung durch eine andere Person und keine "
        "Ground Truth.\n\n"
        f"- Erzeugt mit `python -m kinderbuch_bildlabor.demo_data build` (Code-Stand `{version}`).\n"
        "- Prüfen: `python -m kinderbuch_bildlabor.demo_data check`.\n"
        "- Herkunft der Prüfungen: PROVENANCE.md; Rechte und Namensnennung: LICENSES.md.\n"
        "- Die Anwendung schreibt nie in diesen Ordner.\n"
    )


def licenses(ids: list[str]) -> str:
    lines = ["# Rechte und Namensnennung", ""]
    for object_id in ids:
        record = store.read_json(store.object_source(object_id).record)
        source = record["source"]
        biblio = record["bibliographic_metadata_from_colibri"]
        lines += [
            f"## {biblio['title']}, Scan {source['scan_number']} ({object_id})",
            "",
            f"- Digitalisat: {source['institution']}, PPN {source['ppn']}, "
            f"Originalansicht {source['viewer_url']}",
            f"- Rechte am Digitalisat (laut Quelldatensatz): {biblio['rights_statement']}",
            f"- Colibri-Klassen: Lizenz {source['colibri_dataset_license']}; Namensnennung: "
            f"{source['colibri_dataset_credit']}. Geändert: Auswahl und hinzugefügte "
            "Prüfentscheidungen.",
            "",
        ]
    lines += [
        "## Weitere Bestandteile",
        "",
        f"- {OPEN_MARK} Lizenz der METS/MODS-Metadaten nach den Bedingungen der "
        "Staatsbibliothek zu Berlin eintragen.",
        f"- {OPEN_MARK} Lizenz der eigenen Prüfangaben (Beschreibungen, Begründungen) festlegen.",
        "- Schriften: SIL Open Font License (static/fonts/OFL-*.txt).",
        "",
    ]
    return "\n".join(lines)


def provenance(folder: Path, ids: list[str], name: str) -> str:
    lines = [
        "# Herkunft der Demonstrationsprüfungen",
        "",
        f"{ATTESTATION} {name}: Jede unten aufgeführte Bestätigung und Entscheidung habe ich "
        "selbst am Bild und an den Quellen getroffen. Es sind Demonstrationsprüfungen, keine "
        "unabhängige Verifikation und keine Ground Truth.",
        "",
    ]
    for object_id in ids:
        record = store.read_json(folder / "data" / "work" / f"{object_id}.json")[
            "record"
        ]
        lines += [f"## {object_id}", ""]
        lines += [
            f"- {e['at']} · {e['by']} · {e['area']}: {e['action']}"
            for e in record.get("review_log", [])
            if "by" in e
        ] or ["- Keine Bestätigungen oder Entscheidungen."]
        if approval := record.get("final_approval"):
            lines.append(f"- Endbestätigung: {approval['by']}, {approval['at']}")
        lines.append("")
    return "\n".join(lines)


def build(source: Path, name: str, target: Path | None = None) -> list[str]:
    """Legt den Demonstrationsstand an; liefert die verbleibenden offenen Punkte."""
    store.refuse_in_demo("Demonstrationsstand anlegen")
    # Erst beim Aufruf auflösen, damit ein geänderter Zielordner auch wirklich gilt
    target = target or TARGET
    source = source.resolve()
    if source == store.ROOT.resolve():
        raise DemoDataError(
            "Bitte einen eigens angelegten Bearbeitungsordner angeben, nicht den Projektordner."
        )
    if name not in ALLOWED_NAMES:
        raise DemoDataError(f"Nicht zugelassener Name: {name}")
    if target.exists():
        raise DemoDataError(
            f"{target} besteht bereits und wird nicht überschrieben. Bitte erst wegsichern."
        )
    work = source / "data" / "work"
    ids = sorted(p.stem for p in work.glob("*.json"))
    if problems := check(source, published=False):
        raise DemoDataError("\n".join(problems))
    for object_id in ids:
        files = [work / f"{object_id}.json"] + [
            source / "exports" / f for f in export_files(object_id)
        ]
        for path in files:
            out = target / path.relative_to(source)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(path.read_bytes())
    store.write_text(target / "README.md", readme(code_version()))
    store.write_text(target / "LICENSES.md", licenses(ids))
    store.write_text(target / "PROVENANCE.md", provenance(target, ids, name))
    store.write_json(
        target / MANIFEST,
        {
            "kind": "Demonstrationsdaten, keine Ground Truth",
            "files": {
                p.relative_to(target).as_posix(): store.sha256(p)
                for p in data_files(target)
            },
        },
    )
    return check(target)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m kinderbuch_bildlabor.demo_data")
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("build")
    make.add_argument("source", type=Path)
    make.add_argument("--bestaetigt-von", required=True, dest="name")
    verify = commands.add_parser("check")
    verify.add_argument("folder", type=Path, nargs="?")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            remaining = build(args.source, args.name)
            print(f"Angelegt: {TARGET}")
        else:
            remaining = check(args.folder or TARGET)
    except DemoDataError as error:
        print(f"Abgebrochen:\n{error}", file=sys.stderr)
        return 1
    for problem in remaining:
        print(f"Offen: {problem}")
    if not remaining:
        print("Geprüft: veröffentlichbar.")
    return 1 if remaining else 0


if __name__ == "__main__":
    raise SystemExit(main())
