import io

import pytest
from PIL import Image

from kinderbuch_bildlabor import imports, store, validate


def pages():
    output = io.BytesIO()
    Image.new("RGB", (12, 18), "white").save(output, "PNG")
    return imports.preview_import([("page.png", output.getvalue())])


def test_import_publication_reload_and_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    fixtures = store.catalog()
    hashes = {src.id: store.sha256(src.record) for src in fixtures}
    sources = imports.commit_import(pages(), {"title": "Eigenes Buch"})
    assert imports.commit_import(pages(), {"title": "Eigenes Buch"}) == sources
    assert len(store.catalog()) == len(fixtures) + 1
    src = sources[0]
    working = store.new_working_copy(src)
    assert working["based_on"]["file"].startswith("imports:")
    assert working["record"]["source"]["ppn"] is None
    findings = validate.run_all(working, src)
    assert not [f for f in findings if f.category == validate.TECHNICAL]
    assert any(f.code == "DESCRIPTION_EMPTY" for f in findings)
    assert any(
        f.code == "OAI_UNAVAILABLE" and f.category == validate.NOT_RUN for f in findings
    )
    store.save_working_copy(working, "Test", tmp_path / "work")
    assert store.load_working_copy(src, tmp_path / "work") == working
    assert hashes == {src.id: store.sha256(src.record) for src in fixtures}


def test_incomplete_bundle_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    before = store.catalog()
    (store.import_root() / "book-incomplete").mkdir(parents=True)
    assert store.catalog() == before


def test_failed_publication_does_not_change_catalog(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    before = store.catalog()

    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(store, "write_json", fail)
    with pytest.raises(OSError):
        imports.commit_import(pages(), {"title": "Test"})
    assert store.catalog() == before
    assert not list(store.import_root().iterdir())


def manifest(version):
    if version == 3:
        return {
            "type": "Manifest",
            "items": [
                {
                    "id": "canvas",
                    "label": {"de": ["Zwei"]},
                    "items": [
                        {
                            "items": [
                                {
                                    "target": "canvas",
                                    "body": {
                                        "type": "Image",
                                        "id": "https://example.org/page.png",
                                    },
                                }
                            ]
                        }
                    ],
                }
            ],
        }
    return {
        "@type": "sc:Manifest",
        "sequences": [
            {
                "canvases": [
                    {
                        "@id": "canvas",
                        "label": "Zwei",
                        "images": [
                            {
                                "on": "canvas",
                                "resource": {
                                    "@type": "dctypes:Image",
                                    "@id": "https://example.org/page.png",
                                },
                            }
                        ],
                    }
                ]
            }
        ],
    }


@pytest.mark.parametrize("version", [2, 3])
def test_iiif_order_and_simple_pages(version):
    parsed = imports.parse_iiif_pages(manifest(version))
    assert parsed == [
        {
            "name": "Zwei",
            "url": "https://example.org/page.png",
            "canvas": "canvas",
            "page_number": 1,
        }
    ]


def test_iiif_composite_rejected():
    data = manifest(3)
    data["items"][0]["items"][0]["items"].append({})
    with pytest.raises(ValueError, match="Seite 1"):
        imports.parse_iiif_pages(data)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://127.0.0.1",
        "http://[::1]",
        "http://169.254.169.254",
        "https://user:password@example.org",
    ],
)
def test_private_urls_rejected(url):
    from kinderbuch_bildlabor.import_transport import public_address

    with pytest.raises(ValueError):
        public_address(url)


def test_pdf_adapter_bounded_arguments(monkeypatch):
    from types import SimpleNamespace

    calls = []
    monkeypatch.setattr(imports, "pdf_available", lambda: True)

    def run(command, **kwargs):
        calls.append((command, kwargs))
        if command[0] == "pdfinfo":
            return SimpleNamespace(stdout="Pages: 2\n")
        from pathlib import Path

        Path(command[-1]).with_suffix(".png").write_bytes(pages()[0]["image"])
        return SimpleNamespace(stdout="")

    monkeypatch.setattr(imports.subprocess, "run", run)
    result = imports.preview_pdf("own.pdf", b"pdf-original")
    assert [page["page_number"] for page in result] == [1, 2]
    assert all(page["original"] == b"pdf-original" for page in result)
    assert all(call[1]["timeout"] <= 60 for call in calls)
    assert calls[1][0][1:5] == ["-f", "1", "-l", "1"]


def test_imported_exports_preserve_identity_and_unknowns(tmp_path, monkeypatch):
    from kinderbuch_bildlabor import export

    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    src = imports.commit_import(pages(), {"title": "Eigenes Buch"})[0]
    working = store.new_working_copy(src)
    result = export.export_json(working, tmp_path / "export.json")
    assert result["based_on"]["file"] == src.reference()
    row = export.csv_rows(working["record"], "now")[0]
    assert row["ppn"] is None and row["colibri_lizenz"] is None
    assert row["metadaten_herkunft"] == "Import: unbekannt"


def test_imported_objects_have_defined_image_reference(tmp_path, monkeypatch):
    """Regression: Annotation und PAGE-XML scheiterten an image_info_url=None."""
    from kinderbuch_bildlabor import annotations, pagexml

    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    upload = imports.commit_import(pages(), {"title": "Eigenes Buch"})[0]
    iiif_page = pages()[0] | {
        "import_kind": "iiif",
        "canvas": "https://example.org/canvas/1",
        "image_url": "https://example.org/iiif/1/full/max/0/default.jpg",
    }
    iiif = imports.commit_import([iiif_page], {"title": "IIIF-Buch"})[0]
    expected = {
        upload.id: f"urn:bildlabor:{upload.id}:image",
        iiif.id: iiif_page["image_url"],
    }
    for src in (upload, iiif):
        record = store.new_working_copy(src)["record"]
        page = annotations.annotation_page(record, "now")
        assert page["items"][0]["target"]["source"] == expected[src.id]
        assert f'imageFilename="{expected[src.id]}"' in pagexml.page_xml(record, "now")


def test_fixture_image_reference_unchanged():
    from kinderbuch_bildlabor import annotations

    src = store.object_source("pilot-001")
    record = store.read_json(src.record)
    assert annotations.image_reference(record) == record["source"][
        "image_info_url"
    ].removesuffix("/info.json")
