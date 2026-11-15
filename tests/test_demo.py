"""Öffentliche Ansicht (BILDLABOR_DEMO=1): das Backend verweigert jedes Schreiben, jeden Netzabruf
und jeden Programmaufruf, auch bei direktem Funktionsaufruf ohne Oberfläche."""

import io
import os
import re
import socket
import subprocess
import sys
import urllib.request

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

from kinderbuch_bildlabor import (
    actions,
    authority,
    backup,
    import_transport,
    imports,
    ocr,
    proposals,
    review,
    similar,
    store,
    ui,
)

APP = str(store.ROOT / "app.py")
PILOT = "pilot-001"
LEAD = "genovefa-scan-022"


def png() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (12, 18), "white").save(output, "PNG")
    return output.getvalue()


def tree(root) -> dict:
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def forbidden(*args, **kwargs):
    raise AssertionError("Netzabruf oder Programmaufruf in der öffentlichen Ansicht")


@pytest.fixture
def demo(tmp_path, monkeypatch):
    """Lokal vorbereiteter Stand (Arbeitskopie, Export, Index, Sicherung), danach nur lesen."""
    data = tmp_path / "data-dir"
    monkeypatch.setattr(store, "DATA_DIR", data)
    monkeypatch.setattr(store, "WORK_DIR", data / "data" / "work")
    monkeypatch.setattr(store, "EXPORT_DIR", data / "exports")
    src = store.object_source(PILOT)
    store.update_working_copy(
        src,
        lambda r: r["image_description"].update(working_description_de="Test") or True,
        "t",
    )
    actions.run_export(PILOT)
    lead = store.object_source(LEAD)

    def decide(r):
        return review.record_decision(
            r,
            review.CLASSIFICATION,
            review.classification_message(r),
            review.decision_options(review.CLASSIFICATION, r)[0],
            "Gerahmte Abbildung, keine Karte.",
            "Testperson",
            review.decision_basis(r, review.CLASSIFICATION),
        )

    store.update_working_copy(lead, decide, "Begründete Entscheidung")
    actions.run_export(LEAD)
    record = store.load_working_copy(src)["record"]
    region = record["region_annotations"][0]
    page = ui.page_image(src.page_image)
    similar.build([(PILOT, region, page)])
    backup.create_backup(tmp_path / "paket.zip")
    pages = imports.preview_import([("seite.png", png())])

    monkeypatch.setattr(store, "DEMO", True)
    for module, name in [
        (subprocess, "run"),
        (subprocess, "Popen"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (urllib.request, "urlopen"),
    ]:
        monkeypatch.setattr(module, name, forbidden)
    return {
        "root": tmp_path,
        "src": src,
        "region": region,
        "page": page,
        "pages": pages,
        "zip": tmp_path / "paket.zip",
    }


OPERATIONS = {
    "write_text": lambda c: store.write_text(store.DATA_DIR / "x.txt", "x"),
    "write_json": lambda c: store.write_json(store.EXPORT_DIR / "x.json", {}),
    "save_working_copy": lambda c: store.save_working_copy(
        store.load_working_copy(c["src"]), "t"
    ),
    "snapshot": lambda c: store.snapshot_working_copy(store.work_path(PILOT)),
    "update_working_copy": lambda c: store.update_working_copy(
        c["src"], lambda r: True, "t"
    ),
    "action_apply": lambda c: actions.apply(PILOT, "Test", lambda r: True),
    "run_export": lambda c: actions.run_export(PILOT),
    "collection_export": lambda c: actions.run_collection_export(),
    "preview_import": lambda c: imports.preview_import([("x.png", png())]),
    "commit_import": lambda c: imports.commit_import(c["pages"], {"title": "Buch"}),
    "preview_pdf": lambda c: imports.preview_pdf("x.pdf", b"%PDF-1.4"),
    "preview_iiif": lambda c: imports.preview_iiif("https://example.org/m.json"),
    "download_iiif": lambda c: imports.download_iiif(
        {"pages": [{"name": "s", "url": "https://example.org/i.jpg"}]}, [0]
    ),
    "fetch_public": lambda c: import_transport.fetch_public("https://example.org/"),
    "ocr_run": lambda c: ocr.run(["tesseract", "--version"]),
    "propose": lambda c: proposals.propose(c["page"]),
    "gnd_search": lambda c: authority.search("Goethe"),
    "similar_new_entry": lambda c: similar.build(
        [(PILOT, {**c["region"], "xywh": [1, 1, 5, 5]}, c["page"])]
    ),
    "backup_download": lambda c: backup.write_backup(io.BytesIO()),
    "backup_create": lambda c: backup.create_backup(c["root"] / "neu.zip"),
    "backup_verify": lambda c: backup.verify_backup(c["zip"]),
    "backup_restore": lambda c: backup.restore_backup(c["zip"], c["root"] / "ziel"),
}


@pytest.mark.parametrize("name", OPERATIONS)
def test_direct_backend_calls_are_refused_and_change_nothing(demo, name):
    before = tree(demo["root"])
    with pytest.raises(store.ReadOnlyDemo):
        OPERATIONS[name](demo)
    assert tree(demo["root"]) == before


def test_migration_on_load_is_refused(demo):
    path = store.work_path(PILOT)
    working = store.read_json(path)
    del working["record"]["second_review"]
    # Älteres Format direkt auf die Platte legen; store.write_json ist gesperrt
    path.write_text(store.json_text(working), encoding="utf-8")
    before = tree(demo["root"])
    with pytest.raises(store.ReadOnlyDemo):
        store.load_working_copy(demo["src"])
    assert tree(demo["root"]) == before


def test_render_probes_are_off_without_processes_or_network(demo):
    assert proposals.available() is False
    with pytest.raises(ocr.OcrUnavailable):
        ocr.available_models()
    with pytest.raises(ocr.OcrUnavailable):
        ocr.run_crop_ocr(demo["page"], "x", [0, 0, 5, 5], "deu", 6)


def test_reading_prepared_data_still_works(demo):
    before = tree(demo["root"])
    working = store.load_working_copy(demo["src"])
    assert working["record"]["image_description"]["working_description_de"] == "Test"
    index = similar.build([(PILOT, demo["region"], demo["page"])])
    assert similar.entry_key(PILOT, demo["region"]) in index
    exported = store.read_json(actions.export_paths(PILOT)[0])
    assert actions.invalid_exports(PILOT, exported) == []
    assert tree(demo["root"]) == before


def open_demo(view: str | None = None) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert not app.exception
    if view:
        app.radio(key="view").set_value(view).run()
        assert not app.exception
    return app


def test_browsing_every_object_writes_nothing_and_hides_private_data(demo):
    before = tree(demo["root"])
    app = open_demo()
    labels = [b.label for b in app.download_button]
    # Weder Sicherung noch die historische Prüfakte aus docs/ergebnis
    assert "Sicherungspaket herunterladen" not in labels
    assert "Erläuterung herunterladen" not in labels
    objects = [src.id for src in store.catalog()]
    assert len(objects) == 6
    for view in objects:
        app = open_demo(view)
    app = open_demo(PILOT)
    assert "JSON herunterladen" in [b.label for b in app.download_button]
    assert any("Export aktuell" in s.value for s in app.success)
    assert tree(demo["root"]) == before


def test_every_visible_button_works_without_errors_or_writes(demo):
    """Nur Navigation und Lesefunktionen bleiben; keine führt zu einer Sperrmeldung."""
    before = tree(demo["root"])
    clicked = 0
    for view in [None, PILOT, LEAD]:
        for key in [b.key for b in open_demo(view).button if b.key]:
            app = open_demo(view)
            if key not in [b.key for b in app.button if not b.disabled]:
                continue
            app.button(key=key).click().run()
            clicked += 1
            assert not app.exception, key
            assert tree(demo["root"]) == before, key
    assert clicked > 20


def test_demo_defaults_to_curated_folder_and_local_mode_is_unchanged():
    env = {k: v for k, v in os.environ.items() if not k.startswith("BILDLABOR_")}
    code = "from kinderbuch_bildlabor import store; print(store.DEMO, store.DATA_DIR)"
    demo = subprocess.run(
        [sys.executable, "-c", code],
        env={**env, "BILDLABOR_DEMO": "1"},
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    local = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert demo == ["True", str(store.ROOT / "demo")]
    assert local == ["False", str(store.ROOT)]


ALLOWED_BUTTON = re.compile(
    r"^(open-|queue-open-|search-open-|matrix-open-|guide-)|^(lead-open|second-open)$"
    r"|-continue$|-roundtrip$"
)
ALLOWED_DOWNLOADS = {
    "JSON herunterladen",
    "CSV herunterladen",
    "Prüfbericht als HTML herunterladen",
}
IMPORT = "Eigenes Buch importieren"
TEXT_KINDS = [
    "markdown",
    "caption",
    "info",
    "warning",
    "error",
    "success",
    "text",
    "code",
]


def all_texts(app: AppTest) -> list[str]:
    return [str(e.value) for kind in TEXT_KINDS for e in getattr(app, kind)]


def assert_public(app: AppTest, view: str) -> None:
    assert not app.exception, view
    assert [b.key for b in app.button if not ALLOWED_BUTTON.search(b.key or "")] == []
    assert {b.label for b in app.download_button} <= ALLOWED_DOWNLOADS
    assert [w.key for w in app.text_input] in ([], ["search-query"])
    for kind in ["text_area", "number_input", "checkbox"]:
        assert len(getattr(app, kind)) == 0, (view, kind)
    assert {m.key for m in app.multiselect} <= {"search-status"}
    # Nur die Auswahl der beiden Objekte im Vergleich
    assert {s.key for s in app.selectbox} <= {"compare-a", "compare-b"}
    assert len(app.get("file_uploader")) == 0
    assert {r.key for r in app.radio} <= {"view", f"{view}-region-choice"}
    texts = all_texts(app)
    assert any("Öffentliche Demo – nur lesbar" in s for s in texts)
    assert not any(str(store.DATA_DIR) in s or str(store.ROOT) in s for s in texts)


def test_public_ui_shows_no_prohibited_controls(demo):
    app = open_demo()
    assert_public(app, "sammlung")
    assert IMPORT not in app.radio(key="view").options
    for src in store.catalog():
        assert_public(open_demo(src.id), src.id)


def test_read_only_workflows_remain_accessible(demo):
    app = open_demo(LEAD)
    labels = [t.label for t in app.tabs]
    assert labels[:3] == ["Übersicht", "Klassifikation", "Regionen"]
    assert "Bibliotheksdaten" in labels
    assert len(app.get("image")) >= 3
    decision = [s.value for s in app.success if "Gerahmte Abbildung" in s.value]
    assert decision and "Festgehalten von Testperson" in decision[0]
    assert "Prüfprotokoll" in [h.value for h in app.subheader]
    assert "Verlauf in Zeitfolge" in [e.label for e in app.expander]
    assert any("Gerahmte Abbildung" in d.value.to_string() for d in app.dataframe)
    assert {b.label for b in app.download_button} == ALLOWED_DOWNLOADS
    app.button(key=f"{LEAD}-roundtrip").click().run()
    assert any(s.value.startswith("Export geprüft") for s in app.success)


def test_local_mode_keeps_full_editing(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "WORK_DIR", tmp_path / "work")
    monkeypatch.setattr(store, "EXPORT_DIR", tmp_path / "exports")
    app = open_demo()
    assert IMPORT in app.radio(key="view").options
    assert "Sicherungspaket herunterladen" in [b.label for b in app.download_button]
    assert not any("Öffentliche Demo" in s for s in all_texts(app))
    app = open_demo(LEAD)
    assert app.text_input(key="reviewer")
    assert app.text_area(key=actions.description_key(LEAD))
    assert app.button(key=f"{LEAD}-export")


def test_unshowable_state_gets_plain_german_message(demo):
    path = store.work_path(PILOT)
    working = store.read_json(path)
    del working["record"]["second_review"]
    path.write_text(store.json_text(working), encoding="utf-8")
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    assert any("in der öffentlichen Demo nicht angezeigt" in i.value for i in app.info)


def test_every_public_object_shows_rights_and_attribution(demo):
    for src in store.catalog():
        app = open_demo(src.id)
        record = store.read_json(src.record)
        rights = record["bibliographic_metadata_from_colibri"]["rights_statement"]
        credit = record["source"]["colibri_dataset_credit"]
        assert "Rechte und Herkunft" in [h.value for h in app.subheader]
        assert any(rights in m.value and credit in m.value for m in app.markdown)
