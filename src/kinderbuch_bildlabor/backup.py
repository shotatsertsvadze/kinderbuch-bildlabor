"""Sicherungspaket der Prüfarbeit: ZIP mit Prüfsummen; Zurückspielen nur in einen neuen Ordner."""

import argparse
import hashlib
import json
import shutil
import stat
import sys
import zipfile
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import IO

from kinderbuch_bildlabor import store

MANIFEST = "BACKUP_MANIFEST.json"


class BackupError(Exception):
    pass


def _roots() -> dict[str, Path]:
    # Nur veränderliche Daten; sammlung/ und die Startdateien sind Quellen und bleiben draußen
    return {
        "data/work": store.WORK_DIR,
        "data/imports": store.import_root(),
        "exports": store.EXPORT_DIR,
    }


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _collect() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for prefix, root in _roots().items():
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and not path.is_symlink():
                files[f"{prefix}/{path.relative_to(root).as_posix()}"] = (
                    path.read_bytes()
                )
    return files


def write_backup(dest: IO[bytes] | Path) -> int:
    with store.LOCK:
        files = _collect()
    manifest = {
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": [
            {"path": p, "size": len(d), "sha256": _sha(d)} for p, d in files.items()
        ],
    }
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2))
        for name, data in files.items():
            zf.writestr(name, data)
    return len(files)


def create_backup(target_zip: Path) -> int:
    target_zip = target_zip.resolve()
    if target_zip.exists():
        raise BackupError(
            f"{target_zip} existiert bereits; es wird nichts überschrieben."
        )
    if any(target_zip.is_relative_to(root.resolve()) for root in _roots().values()):
        raise BackupError("Das Paket darf nicht in einem gesicherten Ordner liegen.")
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    tmp = target_zip.with_name(target_zip.name + ".tmp")
    try:
        count = write_backup(tmp)
        tmp.replace(target_zip)
    finally:
        tmp.unlink(missing_ok=True)
    return count


def _unsafe(name: str) -> bool:
    p = PurePosixPath(name)
    return (
        p.is_absolute()
        or "\\" in name
        or any(part in ("..", "") for part in name.split("/"))
        or p.parts[0] not in ("data", "exports")
    )


def _manifest(zf: zipfile.ZipFile) -> dict[str, dict]:
    try:
        data = json.loads(zf.read(MANIFEST))
        return {e["path"]: e for e in data["files"]}
    except (KeyError, ValueError, TypeError) as exc:
        raise BackupError("Manifest fehlt oder ist unlesbar.") from exc


def _problems(zf: zipfile.ZipFile) -> list[str]:
    expected = _manifest(zf)
    problems: list[str] = []
    seen: set[str] = set()
    for info in zf.infolist():
        name = info.filename
        if name == MANIFEST or info.is_dir():
            continue
        if _unsafe(name) or stat.S_ISLNK(info.external_attr >> 16):
            problems.append(f"Unzulässiger Eintrag: {name}")
            continue
        seen.add(name)
        entry = expected.get(name)
        if entry is None:
            problems.append(f"Nicht im Manifest: {name}")
        elif _sha(zf.read(info)) != entry["sha256"]:
            problems.append(f"Prüfsumme weicht ab: {name}")
    problems += [f"Fehlt im Paket: {p}" for p in expected if p not in seen]
    return problems


def verify_backup(zip_file: Path | IO[bytes]) -> list[str]:
    try:
        with zipfile.ZipFile(zip_file) as zf:
            return _problems(zf)
    except zipfile.BadZipFile as exc:
        raise BackupError("Keine gültige ZIP-Datei.") from exc


def restore_backup(zip_path: Path, target_dir: Path) -> int:
    target_dir = target_dir.resolve()
    if target_dir.exists() and (not target_dir.is_dir() or any(target_dir.iterdir())):
        raise BackupError(f"{target_dir} ist nicht leer; es wird nichts überschrieben.")
    problems = verify_backup(zip_path)
    if problems:
        raise BackupError("Paket ist nicht intakt:\n" + "\n".join(problems))
    staging = target_dir.with_name(f".{target_dir.name}.staging")
    if staging.exists():
        raise BackupError(f"{staging} existiert; bitte prüfen und entfernen.")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            expected = _manifest(zf)
            for name, entry in expected.items():
                data = zf.read(name)
                if _sha(data) != entry["sha256"]:
                    raise BackupError(f"Prüfsumme weicht ab: {name}")
                out = staging / name
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(data)
        if target_dir.exists():
            target_dir.rmdir()
        staging.rename(target_dir)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return len(expected)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kinderbuch_bildlabor.backup")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("create").add_argument("zip", type=Path)
    sub.add_parser("verify").add_argument("zip", type=Path)
    restore = sub.add_parser("restore")
    restore.add_argument("zip", type=Path)
    restore.add_argument("target", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            print(f"{create_backup(args.zip)} Dateien gesichert: {args.zip}")
        elif args.command == "verify":
            problems = verify_backup(args.zip)
            print("\n".join(problems) if problems else "Paket ist intakt.")
            return 1 if problems else 0
        else:
            count = restore_backup(args.zip, args.target)
            print(
                f"{count} Dateien zurückgespielt. Start mit BILDLABOR_DATA_DIR={args.target}"
            )
    except BackupError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
