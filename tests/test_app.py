"""Oberflächentests mit Streamlit AppTest; alle Daten liegen in einem Temp-Ordner."""

import pytest
from streamlit.testing.v1 import AppTest

from kinderbuch_bildlabor import review, store

APP = str(store.ROOT / "app.py")
PILOT = "pilot-001"
REGION_1 = "pilot-001-region-01"
DESCRIPTION = f"{PILOT}-description"
TITLE = f"{PILOT}-working_title"
PUBLISHER = f"{PILOT}-working_publisher_statement"


@pytest.fixture(autouse=True)
def temp_data(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "WORK_DIR", tmp_path / "work")
    monkeypatch.setattr(store, "EXPORT_DIR", tmp_path / "exports")
    return tmp_path


def open_app(view: str = PILOT) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert not app.exception
    if view != "sammlung":
        app.radio(key="view").set_value(view).run()
        assert not app.exception
    return app


def saved(object_id: str = PILOT) -> dict:
    return store.read_json(store.work_path(object_id))


def confirm(app: AppTest, key: str, name: str = "Testperson") -> None:
    app.text_input(key="reviewer").input(name).run()
    app.checkbox(key=f"{key}-review-check").check().run()
    app.button(key=f"{key}-review-confirm").click().run()


def save_description(app: AppTest, text: str) -> None:
    app.text_area(key=DESCRIPTION).input(text).run()
    app.button(key=f"{DESCRIPTION}-save").click().run()


def texts(app: AppTest, kind: str) -> list[str]:
    return [element.value for element in getattr(app, kind)]


def test_start_page_lists_six_objects_from_two_books_and_writes_nothing():
    app = open_app("sammlung")
    assert "#### Stichprobe: 6 Illustrationen aus 2 Büchern" in texts(app, "markdown")
    assert len([b for b in app.button if b.key.startswith("open-")]) == 6
    app.button(key="open-genovefa-scan-014").click().run()
    assert app.radio(key="view").value == "genovefa-scan-014"
    assert not app.exception
    assert not store.WORK_DIR.exists()


def test_second_session_keeps_confirmation_of_first_session():
    tab_a, tab_b = open_app(), open_app()
    confirm(tab_a, REGION_1)
    save_description(tab_b, "Neue Beschreibung")

    record = saved()["record"]
    assert review.find_region(record, REGION_1)["review_status"] == review.REGION_REVIEWED
    assert record["image_description"]["working_description_de"] == "Neue Beschreibung"
    assert [e.get("by") for e in record["review_log"]] == ["Testperson", None]


def test_unchanged_text_cannot_be_saved_and_writes_nothing():
    app = open_app()
    app.text_area(key=DESCRIPTION).input(app.text_area(key=DESCRIPTION).value + "  ").run()
    assert app.button(key=f"{DESCRIPTION}-save").disabled
    assert not store.work_path(PILOT).exists()


def test_confirmation_is_refused_when_coordinates_changed_elsewhere():
    tab_a, tab_b = open_app(), open_app()
    tab_a.text_input(key="reviewer").input("Testperson").run()
    tab_a.checkbox(key=f"{REGION_1}-review-check").check().run()
    tab_b.number_input(key=f"{REGION_1}-w").set_value(900).run()
    tab_b.button(key=f"{REGION_1}-save").click().run()

    # Fenster A bestätigt die Ansicht, die es zuletzt gezeigt hat (alte Koordinaten)
    tab_a.button(key=f"{REGION_1}-review-confirm").click().run()

    region = review.find_region(saved()["record"], REGION_1)
    assert region["xywh"] == [210, 260, 900, 1365]
    assert region["review_status"] == review.REGION_DRAFT


def test_edit_after_confirmation_resets_only_that_region():
    app = open_app()
    confirm(app, REGION_1)
    app.number_input(key=f"{REGION_1}-w").set_value(920).run()
    app.button(key=f"{REGION_1}-save").click().run()

    record = saved()["record"]
    assert [r["review_status"] for r in record["region_annotations"]] == [review.REGION_DRAFT] * 3
    assert review.find_region(record, REGION_1)["keyword_review_status"] == review.KEYWORDS_ACCEPTED
    assert set(record["transcription"]["review_status_by_field"].values()) == {review.TRANSCRIPTION_PROVISIONAL}


def test_description_confirmation_is_reset_by_edit_and_keeps_other_areas():
    app = open_app()
    confirm(app, DESCRIPTION)
    assert saved()["record"]["image_description"]["review_status"] == review.DESCRIPTION_REVIEWED
    save_description(app, "Geänderte Beschreibung")
    record = saved()["record"]
    assert record["image_description"]["review_status"] == review.DESCRIPTION_OPEN
    assert review.find_region(record, REGION_1)["keyword_review_status"] == review.KEYWORDS_ACCEPTED


def roundtrip_messages(app: AppTest) -> list[str]:
    return [m for m in texts(app, "success") + texts(app, "error") if m.startswith(("Erhalten:", "Abweichung:"))]


def test_export_becomes_stale_after_confirmation_and_current_after_new_export():
    app = open_app()
    app.button(key=f"{PILOT}-export").click().run()
    confirm(app, REGION_1)
    assert any(w.startswith("Export veraltet") for w in texts(app, "warning"))
    assert app.button(key=f"{PILOT}-roundtrip").disabled

    app.button(key=f"{PILOT}-export").click().run()
    app.button(key=f"{PILOT}-roundtrip").click().run()
    messages = roundtrip_messages(app)
    assert len(messages) == 5 and all(m.startswith("Erhalten:") for m in messages)


def test_real_content_difference_in_current_export_is_reported():
    app = open_app()
    app.button(key=f"{PILOT}-export").click().run()
    path = store.EXPORT_DIR / "pilot-001.json"
    data = store.read_json(path)
    data["record"]["ocr_result"]["raw_text"] = data["record"]["ocr_result"]["raw_text"].replace("„", '"')
    store.write_json(path, data)

    app.button(key=f"{PILOT}-roundtrip").click().run()
    failed = [m for m in roundtrip_messages(app) if m.startswith("Abweichung:")]
    assert failed == ["Abweichung: Unicode-Texte unverändert (z. B. ‘ „ ä ß ×)",
                      "Abweichung: Gesamter Datensatz identisch"]
    assert any("`ocr_result › raw_text`" in m for m in texts(app, "markdown"))


def test_restart_shows_saved_confirmation_with_name():
    confirm(open_app(), REGION_1, name="Testperson")
    restarted = open_app()
    assert any("Bestätigt von Testperson" in s for s in texts(restarted, "success"))


def test_region_choice_labels_stay_stable_after_confirmation():
    """Ändert sich die Beschriftung, verliert der Browser die Auswahl (im Browser nachgewiesen)."""
    app = open_app()
    before = app.radio(key=f"{PILOT}-region-choice").options
    confirm(app, REGION_1)
    assert app.radio(key=f"{PILOT}-region-choice").options == before


def test_multiline_description_is_shown_unchanged():
    app = open_app()
    save_description(app, "Zeile eins\nZeile *zwei*")
    assert "Zeile eins\nZeile *zwei*" in texts(app, "text")


def test_title_can_be_confirmed_without_publisher_statement():
    app = open_app()
    confirm(app, TITLE)
    status = saved()["record"]["transcription"]["review_status_by_field"]
    assert status == {"working_title": review.TRANSCRIPTION_REVIEWED,
                      "working_publisher_statement": review.TRANSCRIPTION_PROVISIONAL}
    assert app.checkbox(key=f"{PUBLISHER}-review-check") is not None


def test_saving_publisher_statement_keeps_title_confirmation():
    app = open_app()
    confirm(app, TITLE)
    app.text_input(key=PUBLISHER).input("Verlag der L.P.Setzer'schen Buchhandlung in Rottweil.").run()
    app.button(key=f"{PUBLISHER}-save").click().run()

    transcription = saved()["record"]["transcription"]
    assert transcription["working_publisher_statement"] == "Verlag der L.P.Setzer'schen Buchhandlung in Rottweil."
    assert transcription["review_status_by_field"]["working_title"] == review.TRANSCRIPTION_REVIEWED


def comparison_table(app: AppTest):
    return next(d.value for d in app.dataframe if "Ergebnis" in d.value.columns)


def test_library_tab_shows_parsing_checks_xsd_and_comparison():
    app = open_app()
    assert "XML-Parsing: erfolgreich" in texts(app, "success")
    assert "Inhaltliche Prüfungen: 7 von 7 bestanden" in texts(app, "success")
    assert "XSD-Validierung: nicht ausgeführt" in texts(app, "info")
    assert list(comparison_table(app)["Ergebnis"]) == ["übereinstimmend"] * 7
    assert not store.work_path(PILOT).exists()


def test_genovefa_object_has_no_transcription_tab_and_shows_draft_origin():
    app = open_app("genovefa-scan-014")
    assert [t.label for t in app.tabs] == ["Übersicht", "Regionen", "Beschreibung", "Bibliotheksdaten",
                                           "Prüfung", "Export"]
    assert any("Entwurf des KI-Assistenten" in c for c in texts(app, "caption"))
    assert "in beiden nicht angegeben" in list(comparison_table(app)["Ergebnis"])
    assert not any("Technische Fehler" in m and ": 0" not in m for m in texts(app, "markdown"))


def test_confirming_ai_keywords_records_person_and_changes_only_that_object():
    app = open_app("genovefa-scan-016")
    confirm(app, "genovefa-scan-016-region-01-keywords")
    region = saved("genovefa-scan-016")["record"]["region_annotations"][0]
    assert region["keyword_review_status"] == review.KEYWORDS_ACCEPTED
    assert saved("genovefa-scan-016")["record"]["review_log"][-1]["by"] == "Testperson"
    assert sorted(p.name for p in store.WORK_DIR.iterdir()) == ["genovefa-scan-016.json"]


def test_stale_tab_cannot_overwrite_newer_description():
    """Nachweis vorher: Fenster A überschrieb die neuere Beschreibung aus Fenster B ohne Hinweis."""
    tab_a, tab_b = open_app(), open_app()
    save_description(tab_b, "Beschreibung aus Fenster B")
    tab_a.text_area(key=DESCRIPTION).input("Beschreibung aus Fenster A").run()

    assert tab_a.button(key=f"{DESCRIPTION}-save").disabled
    assert any("anderen Fenster" in e for e in texts(tab_a, "error"))
    assert saved()["record"]["image_description"]["working_description_de"] == "Beschreibung aus Fenster B"

    tab_a.button(key=f"{DESCRIPTION}-reload").click().run()
    assert tab_a.text_area(key=DESCRIPTION).value == "Beschreibung aus Fenster B"


def test_click_from_outdated_page_is_refused_by_the_store():
    tab_a, tab_b = open_app(), open_app()
    tab_a.text_area(key=DESCRIPTION).input("Beschreibung aus Fenster A").run()
    save_description(tab_b, "Beschreibung aus Fenster B")
    tab_a.button(key=f"{DESCRIPTION}-save").click().run()

    assert saved()["record"]["image_description"]["working_description_de"] == "Beschreibung aus Fenster B"
    assert any("inzwischen an anderer Stelle geändert" in e for e in texts(tab_a, "error"))


def test_untouched_tab_follows_saved_keywords_without_false_unsaved_warning():
    """Nachweis vorher: das andere Fenster zeigte alte Begriffe als „Ungespeicherte Eingabe“."""
    tab_c, tab_d = open_app(), open_app()
    tab_d.text_area(key=f"{REGION_1}-keywords").input("Baum\nLandschaft").run()
    tab_d.button(key=f"{REGION_1}-keywords-save").click().run()
    tab_c.run()

    assert tab_c.text_area(key=f"{REGION_1}-keywords").value == "Baum\nLandschaft"
    assert not any(w.startswith("Ungespeicherte") for w in texts(tab_c, "warning"))


def test_collection_export_has_one_row_per_region_of_all_objects():
    import csv
    app = open_app("sammlung")
    app.button(key="collection-export").click().run()
    with (store.EXPORT_DIR / "sammlung.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3 + 5
    assert {r["ppn"] for r in rows} == {"PPN1814684999", "PPN1772789429"}
    assert all(r["colibri_lizenz"] == "https://creativecommons.org/licenses/by/4.0/" for r in rows)
    assert not store.WORK_DIR.exists()
