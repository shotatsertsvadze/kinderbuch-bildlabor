import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

from kinderbuch_bildlabor import store
from kinderbuch_bildlabor.import_transport import fetch_public

MAX_BYTES = 50 * 1024 * 1024
MAX_PAGES = 200


def preview_import(files: list[tuple[str, bytes]]) -> list[dict]:
    if not files or len(files) > MAX_PAGES:
        raise ValueError("Bitte 1–200 JPEG/PNG-Seiten auswählen.")
    pages = []
    for name, content in files:
        if len(content) > MAX_BYTES:
            raise ValueError("Eine Datei überschreitet 50 MiB.")
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise ValueError("Nur JPEG/PNG-Bilder sind unterstützt.")
            normalized = ImageOps.exif_transpose(image).convert("RGB")
            output = io.BytesIO()
            normalized.save(output, format="PNG")
        pages.append(
            {
                "name": name,
                "original": content,
                "image": output.getvalue(),
                "size": normalized.size,
            }
        )
    return pages


def imported_record(object_id: str, page: dict, number: int, metadata: dict) -> dict:
    width, height = page["size"]
    return {
        "id": object_id,
        "source_profile": "imported",
        "status": "draft_pending_final_review",
        "recorded_on": store.now_utc(),
        "metadata_provenance": {"kind": "user_import", **metadata},
        "source": {
            "institution": metadata.get("source"),
            "ppn": None,
            "physical_page_id": None,
            "scan_number": number,
            "printed_page_number": None,
            "image_width": width,
            "image_height": height,
            "viewer_url": None,
            "image_info_url": None,
            "colibri_file_reference": None,
            "colibri_dataset_license": None,
            "colibri_dataset_credit": None,
        },
        "bibliographic_metadata_from_colibri": {
            "title": metadata["title"],
            "author_display": None,
            "publication_place": None,
            "publication_date": None,
            "publisher": None,
            "rights_statement": metadata.get("rights"),
        },
        "image_description": {
            "object_type": "Abbildung",
            "observation_de": "",
            "working_description_de": "",
            "illustrator": None,
            "review_status": "unreviewed",
        },
        "review_items": [],
        "region_annotations": [
            {
                "id": object_id + "-region-01",
                "label_de": "Illustration",
                "region_type": "illustration",
                "xywh": [0, 0, width, height],
                "coordinate_unit": "pixel",
                "review_status": "draft_pending_visual_review",
                "region_origin_de": "Vollseite beim Import; noch nicht geprüft",
            }
        ],
    }


def commit_import(pages: list[dict], metadata: dict) -> list[store.ObjectSource]:
    if not pages or len(pages) > MAX_PAGES or not metadata.get("title", "").strip():
        raise ValueError("Seiten und Buchtitel sind erforderlich.")
    digest = hashlib.sha256()
    digest.update(json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode())
    for page in pages:
        digest.update(hashlib.sha256(page["original"]).digest())
        digest.update(str(page.get("page_number", "")).encode())
    bundle_id = "book-" + digest.hexdigest()
    root = store.import_root()
    root.mkdir(parents=True, exist_ok=True)
    target = root / bundle_id
    with store.LOCK:
        if not target.exists():
            with tempfile.TemporaryDirectory(prefix=".staging-", dir=root) as temporary:
                staging = Path(temporary) / bundle_id
                staging.mkdir()
                objects = []
                for number, page in enumerate(pages, 1):
                    object_id = f"{bundle_id}-{number:04d}"
                    prefix = f"{number:04d}"
                    (staging / f"{prefix}.original").write_bytes(page["original"])
                    (staging / f"{prefix}.png").write_bytes(page["image"])
                    record = imported_record(
                        object_id, page, page.get("page_number", number), metadata
                    )
                    record["metadata_provenance"].update(
                        {
                            key: page[key]
                            for key in (
                                "import_kind",
                                "canvas",
                                "image_url",
                                "page_number",
                            )
                            if key in page
                        }
                    )
                    record["metadata_provenance"]["original_filename"] = page["name"]
                    store.write_json(staging / f"{prefix}.json", record)
                    objects.append(
                        {
                            "id": object_id,
                            "record": f"{prefix}.json",
                            "page_image": f"{prefix}.png",
                            "image_info": "unavailable",
                            "oai_record": "unavailable",
                            "manifest": "MANIFEST.json",
                        }
                    )
                store.write_json(
                    staging / "MANIFEST.json",
                    {
                        "files": [
                            {"file": path.name, "sha256": store.sha256(path)}
                            for path in sorted(staging.iterdir())
                        ]
                    },
                )
                store.write_json(staging / "bundle.json", {"objects": objects})
                for path in staging.iterdir():
                    with path.open("rb") as handle:
                        os.fsync(handle.fileno())
                staging.rename(target)
        ids = {
            entry["id"] for entry in store.read_json(target / "bundle.json")["objects"]
        }
        return [src for src in store.catalog() if src.id in ids]


def pdf_available() -> bool:
    return bool(shutil.which("pdfinfo") and shutil.which("pdftoppm"))


def preview_pdf(name: str, content: bytes) -> list[dict]:
    if not pdf_available():
        raise ValueError(
            "PDF-Import benötigt lokal Poppler (pdfinfo und pdftoppm im PATH). JPEG/PNG bleiben nutzbar."
        )
    if len(content) > MAX_BYTES:
        raise ValueError("PDF überschreitet 50 MiB.")
    with tempfile.TemporaryDirectory() as directory:
        pdf = Path(directory) / "input.pdf"
        pdf.write_bytes(content)
        info = subprocess.run(
            ["pdfinfo", str(pdf)],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        count = next(
            (
                int(line.split(":", 1)[1])
                for line in info.stdout.splitlines()
                if line.startswith("Pages:")
            ),
            0,
        )
        if not 1 <= count <= MAX_PAGES:
            raise ValueError("PDF muss 1–200 Seiten enthalten.")
        pages = []
        for number in range(1, count + 1):
            prefix = Path(directory) / "page"
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    str(number),
                    "-l",
                    str(number),
                    "-singlefile",
                    "-scale-to",
                    "4000",
                    "-png",
                    str(pdf),
                    str(prefix),
                ],
                capture_output=True,
                timeout=60,
                check=True,
            )
            page = preview_import(
                [(f"{name} · Seite {number}", prefix.with_suffix(".png").read_bytes())]
            )[0]
            page.update(original=content, page_number=number, import_kind="pdf")
            pages.append(page)
        return pages


def iiif_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " / ".join(
            str(text)
            for texts in value.values()
            for text in (texts if isinstance(texts, list) else [texts])
        )
    return ""


def parse_iiif_pages(manifest: dict) -> list[dict]:
    if manifest.get("type") == "Manifest":
        canvases = manifest.get("items", [])
        version = 3
    elif manifest.get("@type") == "sc:Manifest":
        sequences = manifest.get("sequences", [])
        if len(sequences) != 1:
            raise ValueError("Nur eine einfache IIIF-Sequenz wird unterstützt.")
        canvases = sequences[0].get("canvases", [])
        version = 2
    else:
        raise ValueError(
            "Eine IIIF Presentation 2/3 Manifest-Adresse ist erforderlich."
        )
    if not 1 <= len(canvases) <= MAX_PAGES:
        raise ValueError("Manifest muss 1–200 einfache Bildseiten enthalten.")
    pages = []
    for number, canvas in enumerate(canvases, 1):
        try:
            if version == 3:
                annotation_pages = canvas["items"]
                if len(annotation_pages) != 1:
                    raise ValueError
                annotations = annotation_pages[0]["items"]
                body = annotations[0]["body"]
            else:
                annotations = canvas["images"]
                body = annotations[0]["resource"]
            if len(annotations) != 1 or not isinstance(body, dict):
                raise ValueError
            if body.get("type", body.get("@type")) not in {"Image", "dctypes:Image"}:
                raise ValueError
            target = annotations[0].get("target", annotations[0].get("on"))
            canvas_id = canvas.get("id", canvas.get("@id"))
            if target != canvas_id or body.get("selector") or body.get("auth"):
                raise ValueError
            services = body.get("service", [])
            services = services if isinstance(services, list) else [services]
            if any("auth" in json.dumps(service).lower() for service in services):
                raise ValueError
            image_url = body.get("id", body.get("@id"))
            if not image_url:
                if len(services) != 1:
                    raise ValueError
                service = services[0]
                base = service.get("id", service.get("@id"))
                size = "max" if service.get("type") == "ImageService3" else "full"
                image_url = f"{base.rstrip('/')}/full/{size}/0/default.jpg"
            pages.append(
                {
                    "name": iiif_text(canvas.get("label")) or f"Seite {number}",
                    "url": image_url,
                    "canvas": canvas_id,
                    "page_number": number,
                }
            )
        except (KeyError, IndexError, TypeError, ValueError, AttributeError) as error:
            raise ValueError(
                f"Seite {number}: zusammengesetzte, authentifizierte oder nicht unterstützte IIIF-Seite."
            ) from error
    return pages


def preview_iiif(url: str) -> dict:
    raw = fetch_public(url, 5 * 1024 * 1024)
    manifest = json.loads(raw)
    return {
        "pages": parse_iiif_pages(manifest),
        "title": iiif_text(manifest.get("label")),
        "rights": iiif_text(manifest.get("rights", manifest.get("license"))),
        "source": url,
        "manifest": raw.decode("utf-8"),
    }


def download_iiif(preview: dict, selected: list[int]) -> list[dict]:
    pages = []
    for index in selected:
        entry = preview["pages"][index]
        page = preview_import([(entry["name"], fetch_public(entry["url"]))])[0]
        page.update(
            page_number=entry["page_number"],
            canvas=entry["canvas"],
            import_kind="iiif",
            image_url=entry["url"],
        )
        pages.append(page)
    return pages
