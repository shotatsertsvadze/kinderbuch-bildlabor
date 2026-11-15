"""Kuratierter Demonstrationsstand: nur vollständige, aktuelle, zugelassene Daten werden übernommen."""

import pytest
from streamlit.testing.v1 import AppTest

from kinderbuch_bildlabor import actions, demo_data, review, store

LEAD = "genovefa-scan-022"
NAME = "Testperson"


def point_store_at(monkeypatch, folder) -> None:
    monkeypatch.setattr(store, "DATA_DIR", folder)
    monkeypatch.setattr(store, "WORK_DIR", folder / "data" / "work")
    monkeypatch.setattr(store, "EXPORT_DIR", folder / "exports")


def decide(by: str, rationale: str = "Gerahmte Abbildung, keine Karte."):
    def change(record):
        return review.record_decision(
            record,
            review.CLASSIFICATION,
            review.classification_message(record),
            review.decision_options(review.CLASSIFICATION, record)[0],
            rationale,
            by,
            review.decision_basis(record, review.CLASSIFICATION),
        )

    return change


REAL_TARGET = store.ROOT / "demo"


@pytest.fixture(autouse=True)
def isolated_target(tmp_path, monkeypatch):
    """Regression: ein Test legte den echten Ordner demo/ an."""
    existed = REAL_TARGET.exists()
    monkeypatch.setattr(demo_data, "TARGET", tmp_path / "demo")
    yield
    assert REAL_TARGET.exists() == existed


@pytest.fixture
def build_dir(tmp_path, monkeypatch):
    """Bearbeitungsordner wie nach einer Prüfsitzung, mit Verlauf und Zwischenspeichern."""
    monkeypatch.setattr(demo_data, "ALLOWED_NAMES", {NAME})
    folder = tmp_path / "build"
    point_store_at(monkeypatch, folder)
    src = store.object_source(LEAD)
    store.update_working_copy(
        src,
        lambda r: (
            r["image_description"].update(working_description_de="Zwei Figuren") or True
        ),
        "Bildbeschreibung",
    )
    store.update_working_copy(src, decide(NAME), "Begründete Entscheidung")
    actions.run_export(LEAD)
    (folder / "authority").mkdir()
    (folder / "authority" / "x.json").write_text("[]")
    (folder / "exports" / actions.COLLECTION_CSV).write_text("privat")
    return folder


def built(build_dir, tmp_path):
    return demo_data.build(build_dir, NAME, tmp_path / "demo")


def test_build_copies_only_curated_files(build_dir, tmp_path):
    remaining = built(build_dir, tmp_path)
    target = tmp_path / "demo"
    files = sorted(
        p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()
    )
    assert files == sorted(
        [
            "MANIFEST.json",
            "README.md",
            "LICENSES.md",
            "PROVENANCE.md",
            f"data/work/{LEAD}.json",
            *(f"exports/{name}" for name in demo_data.export_files(LEAD)),
        ]
    )
    for name in demo_data.export_files(LEAD):
        assert (target / "exports" / name).read_bytes() == (
            build_dir / "exports" / name
        ).read_bytes()
    # Offen bleiben nur die Lizenzangaben, die die veröffentlichende Person selbst einträgt
    assert remaining == ["LICENSES.md enthält noch offene Angaben (OFFEN:)."]
    licences = target / "LICENSES.md"
    text = licences.read_text("utf-8")
    assert "Public Domain Mark 1.0" in text and "CC BY 4.0" not in text
    assert "creativecommons.org/licenses/by/4.0" in text and "Schmideler" in text
    licences.write_text(text.replace(demo_data.OPEN_MARK, "Festgelegt:"), "utf-8")
    assert demo_data.check(target) == []
    provenance = (target / "PROVENANCE.md").read_text("utf-8")
    assert f"{demo_data.ATTESTATION} {NAME}" in provenance
    assert "Gerahmte Abbildung, keine Karte." in provenance
    assert "keine Ground Truth" in (target / "README.md").read_text("utf-8")


@pytest.mark.parametrize(
    "spoil, message",
    [
        (
            lambda d: store.update_working_copy(
                store.object_source(LEAD),
                lambda r: (
                    r["image_description"].update(working_description_de="Neu") or True
                ),
                "Bildbeschreibung",
            ),
            "Export entspricht nicht dem letzten Arbeitsstand",
        ),
        (
            lambda d: (d / "exports" / f"{LEAD}.page.xml").write_text("<x/>"),
            "Exportdateien passen nicht zusammen",
        ),
        (lambda d: (d / "exports" / f"{LEAD}.json").unlink(), "Export fehlt"),
        (
            lambda d: (
                store.update_working_copy(
                    store.object_source(LEAD),
                    decide("ShotaTest", "Testeintrag."),
                    "Begründete Entscheidung",
                )
                and actions.run_export(LEAD)
            ),
            "Nicht zugelassene Namen: ['ShotaTest']",
        ),
    ],
)
def test_build_refuses_unpublishable_states(build_dir, tmp_path, spoil, message):
    spoil(build_dir)
    with pytest.raises(demo_data.DemoDataError, match=message.replace("[", r"\[")):
        built(build_dir, tmp_path)
    assert not (tmp_path / "demo").exists()


def test_build_refuses_older_format_working_copy(build_dir, tmp_path):
    path = store.work_path(LEAD)
    working = store.read_json(path)
    del working["record"]["second_review"]
    path.write_text(store.json_text(working), encoding="utf-8")
    with pytest.raises(demo_data.DemoDataError, match="älteren Format"):
        built(build_dir, tmp_path)


def test_build_refuses_project_folder_existing_target_names_and_demo_mode(
    build_dir, tmp_path, monkeypatch
):
    with pytest.raises(demo_data.DemoDataError, match="Projektordner"):
        demo_data.build(store.ROOT, NAME, tmp_path / "demo")
    with pytest.raises(demo_data.DemoDataError, match="Nicht zugelassener Name"):
        demo_data.build(build_dir, "Jemand", tmp_path / "demo")
    (tmp_path / "demo").mkdir()
    with pytest.raises(demo_data.DemoDataError, match="nicht überschrieben"):
        built(build_dir, tmp_path)
    monkeypatch.setattr(store, "DEMO", True)
    with pytest.raises(store.ReadOnlyDemo):
        demo_data.build(build_dir, NAME, tmp_path / "other")


def test_check_detects_tampering_and_unlisted_files(build_dir, tmp_path):
    built(build_dir, tmp_path)
    target = tmp_path / "demo"
    work = target / "data" / "work" / f"{LEAD}.json"
    work.write_bytes(work.read_bytes() + b" ")
    (target / "data" / "work" / ".history").mkdir()
    (target / "data" / "work" / ".history" / "alt.json").write_text("{}")
    problems = demo_data.check(target)
    assert any("Prüfsummen" in p for p in problems)
    assert "Nicht zugelassene Datei: data/work/.history/alt.json" in problems


def test_public_demo_reads_the_built_folder(build_dir, tmp_path, monkeypatch):
    built(build_dir, tmp_path)
    point_store_at(monkeypatch, tmp_path / "demo")
    monkeypatch.setattr(store, "DEMO", True)
    app = AppTest.from_file(str(store.ROOT / "app.py"), default_timeout=30).run()
    app.radio(key="view").set_value(LEAD).run()
    assert not app.exception
    assert any("Export aktuell" in s.value for s in app.success)
    assert any("Festgehalten von Testperson" in s.value for s in app.success)


def test_committed_demo_folder_is_publishable():
    if not REAL_TARGET.exists():
        pytest.skip(
            "demo/ ist noch nicht angelegt (Schritt 4 durch die prüfende Person)."
        )
    assert demo_data.check(REAL_TARGET) == []


def test_command_line_build_and_check(build_dir, tmp_path, capsys):
    target = tmp_path / "demo"
    assert demo_data.main(["build", str(build_dir), "--bestaetigt-von", NAME]) == 1
    assert "Offen: LICENSES.md enthält noch offene Angaben" in capsys.readouterr().out
    licences = target / "LICENSES.md"
    licences.write_text(
        licences.read_text("utf-8").replace("OFFEN:", "Festgelegt:"), "utf-8"
    )
    assert demo_data.main(["check", str(target)]) == 0
    assert "Geprüft: veröffentlichbar." in capsys.readouterr().out
    assert demo_data.main(["build", str(build_dir), "--bestaetigt-von", NAME]) == 1
    assert "nicht überschrieben" in capsys.readouterr().err
