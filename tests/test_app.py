"""Oberflächentests mit Streamlit AppTest; alle Daten liegen in einem Temp-Ordner."""

import pytest
from streamlit.testing.v1 import AppTest

from kinderbuch_bildlabor import review, store

APP = str(store.ROOT / "app.py")
REGION_1 = "pilot-001-region-01"


@pytest.fixture(autouse=True)
def temp_data(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "WORK_DIR", tmp_path / "work")
    monkeypatch.setattr(store, "EXPORT_DIR", tmp_path / "exports")
    return tmp_path


def open_app() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert not app.exception
    return app


def saved() -> dict:
    return store.read_json(store.work_path("pilot-001"))


def confirm_region_1(app: AppTest, name: str = "Testperson") -> None:
    app.text_input(key="reviewer").input(name).run()
    app.checkbox(key=f"{REGION_1}-review-check").check().run()
    app.button(key=f"{REGION_1}-review-confirm").click().run()


def test_second_session_keeps_confirmation_of_first_session():
    tab_a, tab_b = open_app(), open_app()
    confirm_region_1(tab_a)
    tab_b.text_area(key="description").input("Neue Beschreibung").run()
    tab_b.button(key="description-save").click().run()

    record = saved()["record"]
    assert review.find_region(record, REGION_1)["review_status"] == review.REGION_REVIEWED
    assert record["image_description"]["working_description_de"] == "Neue Beschreibung"
    assert [e.get("by") for e in record["review_log"]] == ["Testperson", None]


def test_saving_unchanged_text_writes_nothing():
    app = open_app()
    app.button(key="description-save").click().run()
    assert not store.work_path("pilot-001").exists()


def test_confirmation_is_refused_when_coordinates_changed_elsewhere():
    tab_a, tab_b = open_app(), open_app()
    tab_a.text_input(key="reviewer").input("Testperson").run()
    tab_a.checkbox(key=f"{REGION_1}-review-check").check().run()
    tab_b.number_input(key=f"{REGION_1}-w").set_value(900).run()
    tab_b.button(key=f"{REGION_1}-save").click().run()

    # Tab A bestätigt die Ansicht, die es zuletzt gezeigt hat (alte Koordinaten)
    tab_a.button(key=f"{REGION_1}-review-confirm").click().run()

    region = review.find_region(saved()["record"], REGION_1)
    assert region["xywh"] == [210, 260, 900, 1365]
    assert region["review_status"] == review.REGION_DRAFT


def test_edit_after_confirmation_resets_only_that_region():
    app = open_app()
    confirm_region_1(app)
    app.number_input(key=f"{REGION_1}-w").set_value(920).run()
    app.button(key=f"{REGION_1}-save").click().run()

    record = saved()["record"]
    assert [r["review_status"] for r in record["region_annotations"]] == [review.REGION_DRAFT] * 3
    assert review.find_region(record, REGION_1)["keyword_review_status"] == review.KEYWORDS_ACCEPTED
    assert set(record["transcription"]["review_status_by_field"].values()) == {review.TRANSCRIPTION_PROVISIONAL}


def roundtrip_messages(app: AppTest) -> list[str]:
    return [m.value for m in [*app.success, *app.error] if m.value.startswith(("Erhalten:", "Abweichung:"))]


def test_export_becomes_stale_after_confirmation_and_current_after_new_export():
    app = open_app()
    app.button(key="export").click().run()
    confirm_region_1(app)
    assert any(w.value.startswith("Export veraltet") for w in app.warning)
    assert app.button(key="roundtrip").disabled

    app.button(key="export").click().run()
    app.button(key="roundtrip").click().run()
    messages = roundtrip_messages(app)
    assert len(messages) == 5 and all(m.startswith("Erhalten:") for m in messages)


def test_unchanged_save_keeps_export_current():
    app = open_app()
    app.button(key="export").click().run()
    app.button(key="description-save").click().run()
    assert any(s.value.startswith("Export aktuell") for s in app.success)


def test_real_content_difference_in_current_export_is_reported():
    app = open_app()
    app.button(key="export").click().run()
    path = store.EXPORT_DIR / "pilot-001.json"
    data = store.read_json(path)
    data["record"]["ocr_result"]["raw_text"] = data["record"]["ocr_result"]["raw_text"].replace("„", '"')
    store.write_json(path, data)

    app.button(key="roundtrip").click().run()
    failed = [m for m in roundtrip_messages(app) if m.startswith("Abweichung:")]
    assert failed == ["Abweichung: Unicode-Texte unverändert (z. B. ‘ „ ä ß ×)",
                      "Abweichung: Gesamter Datensatz identisch"]
    assert any("`ocr_result › raw_text`" in m.value for m in app.markdown)


def test_restart_shows_saved_confirmation_with_name():
    confirm_region_1(open_app(), name="Testperson")
    restarted = open_app()
    assert "Bestätigt von Testperson" in " ".join(c.value for c in restarted.caption)
    assert any("Erledigt: Grenzen visuell geprüft" in m.value for m in restarted.markdown)


def test_region_choice_labels_stay_stable_after_confirmation():
    """Ändert sich die Beschriftung, verliert der Browser die Auswahl (im Browser nachgewiesen)."""
    app = open_app()
    before = app.radio(key="region-choice").options
    confirm_region_1(app)
    assert app.radio(key="region-choice").options == before


def test_multiline_description_is_shown_unchanged():
    app = open_app()
    app.text_area(key="description").input("Zeile eins\nZeile *zwei*").run()
    app.button(key="description-save").click().run()
    assert "Zeile eins\nZeile *zwei*" in [t.value for t in app.text]


def test_title_can_be_confirmed_without_publisher_statement():
    app = open_app()
    app.text_input(key="reviewer").input("Testperson").run()
    app.checkbox(key="working_title-review-check").check().run()
    app.button(key="working_title-review-confirm").click().run()

    status = saved()["record"]["transcription"]["review_status_by_field"]
    assert status == {"working_title": review.TRANSCRIPTION_REVIEWED,
                      "working_publisher_statement": review.TRANSCRIPTION_PROVISIONAL}
    assert app.checkbox(key="working_publisher_statement-review-check") is not None


def test_saving_publisher_statement_keeps_title_confirmation():
    app = open_app()
    app.text_input(key="reviewer").input("Testperson").run()
    app.checkbox(key="working_title-review-check").check().run()
    app.button(key="working_title-review-confirm").click().run()
    app.text_input(key="working_publisher_statement").input("Verlag der L.P.Setzer'schen Buchhandlung in Rottweil.").run()
    app.button(key="working_publisher_statement-save").click().run()

    transcription = saved()["record"]["transcription"]
    assert transcription["working_publisher_statement"] == "Verlag der L.P.Setzer'schen Buchhandlung in Rottweil."
    assert transcription["review_status_by_field"]["working_title"] == review.TRANSCRIPTION_REVIEWED


def test_library_tab_shows_parsing_checks_xsd_and_comparison():
    app = open_app()
    assert "XML-Parsing: erfolgreich" in [s.value for s in app.success]
    assert "Inhaltliche Prüfungen: 7 von 7 bestanden" in [s.value for s in app.success]
    assert "XSD-Validierung: nicht ausgeführt" in [i.value for i in app.info]
    comparison = app.dataframe[0].value
    assert list(comparison["Ergebnis"]) == ["übereinstimmend"] * 7
    assert not store.work_path("pilot-001").exists()
