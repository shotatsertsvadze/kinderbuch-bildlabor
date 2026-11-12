"""Zweite Lesung mit lokal installiertem Tesseract: ausdrücklich gestartet, nie automatisch."""

import difflib
import hashlib
import io
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from kinderbuch_bildlabor import regions
from kinderbuch_bildlabor.store import now_utc

TIMEOUT = 60
MODES = {7: "Einzelzeile (PSM 7)", 6: "Textblock (PSM 6)"}


class OcrUnavailable(Exception):
    pass


def executable() -> str:
    path = os.environ.get("BILDLABOR_TESSERACT") or shutil.which("tesseract")
    if not path:
        raise OcrUnavailable(
            "Tesseract ist nicht installiert. Installieren Sie es lokal (zum Beispiel "
            "mit Homebrew) oder setzen Sie BILDLABOR_TESSERACT; die manuelle Transkription bleibt nutzbar."
        )
    return path


def tessdata_args() -> list[str]:
    folder = os.environ.get("BILDLABOR_TESSDATA")
    return ["--tessdata-dir", folder] if folder else []


def run(arguments: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            arguments, capture_output=True, text=True, timeout=TIMEOUT, check=True
        )
    except subprocess.TimeoutExpired as error:
        raise OcrUnavailable(
            f"Tesseract brauchte länger als {TIMEOUT} Sekunden."
        ) from error
    except (subprocess.CalledProcessError, OSError) as error:
        detail = getattr(error, "stderr", "") or str(error)
        raise OcrUnavailable(
            f"Tesseract ist fehlgeschlagen: {detail.strip()}"
        ) from error


def listing(exe: str) -> tuple[list[str], Path | None]:
    out = run([exe, *tessdata_args(), "--list-langs"])
    text = out.stdout + out.stderr
    folder = re.search(r'languages in "([^"]+)"', text)
    models = [
        line.strip()
        for line in text.splitlines()[1:]
        if line.strip() and line.strip() != "osd"
    ]
    return models, Path(folder.group(1)) if folder else None


def available_models() -> list[str]:
    return listing(executable())[0]


def engine_version(exe: str) -> str:
    out = run([exe, "--version"])
    return (out.stdout or out.stderr).splitlines()[0].strip()


def crop_png(image: Image.Image, xywh: list[int]) -> bytes:
    output = io.BytesIO()
    regions.crop(image, xywh).convert("RGB").save(output, "PNG")
    return output.getvalue()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_crop_ocr(
    image: Image.Image, image_sha256: str, xywh: list[int], model: str, psm: int
) -> dict:
    exe = executable()
    models, folder = listing(exe)
    if model not in models:
        raise OcrUnavailable(f"Das Modell „{model}“ ist nicht installiert.")
    if psm not in MODES:
        raise ValueError("Unbekannter Segmentierungsmodus.")
    png = crop_png(image, xywh)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "crop.png"
        path.write_bytes(png)
        out = run(
            [exe, str(path), "stdout", *tessdata_args(), "-l", model, "--psm", str(psm)]
        )
    model_file = folder / f"{model}.traineddata" if folder else None
    return {
        "text": out.stdout.rstrip("\n"),
        "engine_version": engine_version(exe),
        "model": model,
        "model_sha256": sha(model_file.read_bytes())
        if model_file and model_file.is_file()
        else None,
        "psm": psm,
        "created_at": now_utc(),
        "image_sha256": image_sha256,
        "crop_sha256": sha(png),
        "xywh": list(xywh),
    }


def text_diff(before: str, after: str) -> list[tuple[str, str]]:
    """Zeichengenaue Unterschiede als (gleich|entfernt|hinzugefügt, Text); keine Bewertung."""
    parts = []
    matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
    for tag, a1, a2, b1, b2 in matcher.get_opcodes():
        if tag == "equal":
            parts.append(("gleich", before[a1:a2]))
            continue
        if a2 > a1:
            parts.append(("entfernt", before[a1:a2]))
        if b2 > b1:
            parts.append(("hinzugefügt", after[b1:b2]))
    return parts
