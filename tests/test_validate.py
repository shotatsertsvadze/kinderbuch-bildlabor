import copy

import pytest

from kinderbuch_bildlabor import review, store, validate


KEYWORDS = ["Personengruppe", "Baum", "Landschaft"]
PILOT = store.object_source("pilot-001")
PUBLISHER = "Verlag der I.P.Setzer'schen Buchhandlung in Rottweil."


def pilot_working() -> dict:
    return store.new_working_copy(PILOT)


def codes(findings, category):
    return {f.code for f in findings if f.category == category}


def test_pilot_has_no_technical_errors_but_open_reviews():
    findings = validate.run_all(pilot_working(), PILOT)
    assert codes(findings, validate.TECHNICAL) == set()
    assert {
        "IMPRINT_CONTEXT",
        "ILLUSTRATOR_ATTRIBUTION",
        "REGION_NOT_REVIEWED",
        "TRANSCRIPTION_PROVISIONAL",
        "RECORD_FINAL_REVIEW",
    } <= codes(findings, validate.REVIEW)
    assert {"XSD_VALIDATION", "OCR_EVALUATION"} <= codes(findings, validate.NOT_RUN)


def test_unknown_illustrator_is_not_an_error():
    record = pilot_working()["record"]
    assert record["image_description"]["illustrator"] is None
    assert validate.check_required(record) == []
    assert validate.unknown_optional_fields(record) == [
        "Illustrator",
        "Gedruckte Seitenzahl",
    ]


def test_missing_required_field_is_technical_error():
    record = pilot_working()["record"]
    record["source"]["ppn"] = ""
    del record["region_annotations"][0]["label_de"]
    assert codes(validate.check_required(record), validate.TECHNICAL) == {
        "MISSING_FIELD",
        "MISSING_REGION_FIELD",
    }


def test_duplicate_ids_are_detected():
    record = pilot_working()["record"]
    assert validate.check_duplicate_ids([record]) == []
    assert codes(
        validate.check_duplicate_ids([record, copy.deepcopy(record)]),
        validate.TECHNICAL,
    ) == {"DUPLICATE_OBJECT_ID", "DUPLICATE_REGION_ID"}


def test_region_outside_image_is_technical_error():
    record = pilot_working()["record"]
    record["region_annotations"][1]["xywh"] = [900, 1640, 550, 80]
    findings = validate.check_regions(record)
    assert [f.code for f in findings] == ["REGION_BOUNDS"]


def test_confirmation_closes_only_its_own_area():
    record = pilot_working()["record"]
    review.confirm_region(
        record, "pilot-001-region-02", "Shota Tsertsvadze", [400, 1640, 550, 80]
    )
    open_regions = [
        f.message_de
        for f in validate.check_open_reviews(record)
        if f.code == "REGION_NOT_REVIEWED"
    ]
    assert len(open_regions) == 2
    assert set(record["transcription"]["review_status_by_field"].values()) == {
        review.TRANSCRIPTION_PROVISIONAL
    }
    assert record["review_log"][-1]["by"] == "Shota Tsertsvadze"


def test_editing_resets_status_of_that_area():
    record = pilot_working()["record"]
    review.confirm_region(
        record, "pilot-001-region-01", "Prüfer", [210, 260, 930, 1365]
    )
    review.set_region_xywh(
        record, "pilot-001-region-01", [210, 260, 920, 1365], [210, 260, 930, 1365]
    )
    assert record["region_annotations"][0]["review_status"] == review.REGION_DRAFT

    review.set_keywords(
        record, "pilot-001-region-01", ["Personengruppe", "Baum"], KEYWORDS
    )
    assert (
        record["region_annotations"][0]["keyword_review_status"]
        == review.KEYWORDS_EDITED
    )
    assert "KEYWORDS_NOT_REVIEWED" in codes(
        validate.check_open_reviews(record), validate.REVIEW
    )


def test_unchanged_values_do_not_reset_status():
    record = pilot_working()["record"]
    review.set_keywords(record, "pilot-001-region-01", KEYWORDS, ["veraltet"])
    assert (
        record["region_annotations"][0]["keyword_review_status"]
        == review.KEYWORDS_ACCEPTED
    )
    assert "review_log" not in record


def test_setters_report_whether_content_changed():
    record = pilot_working()["record"]
    text = record["image_description"]["working_description_de"]
    assert review.set_description(record, text, "veraltet") is False
    assert review.set_description(record, "Zeile eins\nZeile *zwei*", text) is True
    assert (
        review.set_transcription(
            record, "working_title", "Die Heimath in Amerika.", "veraltet"
        )
        is False
    )
    assert "review_log" in record and len(record["review_log"]) == 1


def test_confirmation_of_outdated_view_is_refused():
    record = pilot_working()["record"]
    with pytest.raises(review.ContentChanged):
        review.confirm_region(
            record, "pilot-001-region-01", "Prüfer", [210, 260, 900, 1365]
        )
    with pytest.raises(review.ContentChanged):
        review.confirm_keywords(record, "pilot-001-region-01", "Prüfer", ["Baum"])
    with pytest.raises(review.ContentChanged):
        review.confirm_transcription(
            record, "working_title", "Prüfer", "Die Heimat in Amerika."
        )
    assert "review_log" not in record


def test_review_areas_list_each_area_separately():
    record = pilot_working()["record"]
    review.confirm_region(record, "pilot-001-region-02", "Prüfer", [400, 1640, 550, 80])
    areas = review.review_areas(record)
    assert [a["done"] for a in areas] == [False, True, False, False, True, False, False]
    assert [a["label_de"] for a in areas][-2:] == [
        "Transkription: Bildtitel",
        "Transkription: Verlagsangabe auf dem Bildblatt",
    ]
    assert review.last_confirmation(record, "pilot-001-region-02")["by"] == "Prüfer"
    assert review.last_confirmation(record, "pilot-001-region-01") is None


def test_title_and_publisher_have_independent_review_status():
    record = pilot_working()["record"]
    status = record["transcription"]["review_status_by_field"]
    review.confirm_transcription(
        record, "working_title", "Prüfer", "Die Heimath in Amerika."
    )
    assert status == {
        "working_title": review.TRANSCRIPTION_REVIEWED,
        "working_publisher_statement": review.TRANSCRIPTION_PROVISIONAL,
    }

    review.set_transcription(
        record,
        "working_publisher_statement",
        "Verlag der L.P.Setzer'schen Buchhandlung in Rottweil.",
        PUBLISHER,
    )
    assert status["working_title"] == review.TRANSCRIPTION_REVIEWED

    review.set_transcription(
        record, "working_title", "Die Heimath in Amerika", "Die Heimath in Amerika."
    )
    assert status["working_title"] == review.TRANSCRIPTION_PROVISIONAL
    assert (
        review.last_confirmation(record, "transcription/working_title")["by"]
        == "Prüfer"
    )


def test_open_transcription_findings_are_reported_per_field():
    record = pilot_working()["record"]
    review.confirm_transcription(
        record, "working_title", "Prüfer", "Die Heimath in Amerika."
    )
    messages = [
        f.message_de
        for f in validate.check_open_reviews(record)
        if f.code == "TRANSCRIPTION_PROVISIONAL"
    ]
    assert len(messages) == 1 and "Verlagsangabe" in messages[0]


def test_oai_source_has_no_findings_for_pilot_and_reports_differences():
    record = pilot_working()["record"]
    assert validate.check_oai_source(record, PILOT.oai_record) == []
    record["bibliographic_metadata_from_colibri"]["publication_date"] = "1851"
    findings = validate.check_oai_source(record, PILOT.oai_record)
    assert [(f.category, f.code) for f in findings] == [
        (validate.REVIEW, "MODS_DIFFERENCE")
    ]
    assert "1850" in findings[0].message_de and "1851" in findings[0].message_de


def test_edit_based_on_outdated_value_is_refused():
    """Nachweis vorher: ein veraltetes Fenster überschrieb eine neuere Beschreibung ohne Hinweis."""
    record = pilot_working()["record"]
    original = record["image_description"]["working_description_de"]
    review.set_description(record, "Stand aus Fenster B", original)
    with pytest.raises(review.ContentChanged):
        review.set_description(record, "Stand aus Fenster A", original)
    with pytest.raises(review.ContentChanged):
        review.set_keywords(record, "pilot-001-region-01", ["Baum"], ["Personengruppe"])
    with pytest.raises(review.ContentChanged):
        review.set_region_xywh(
            record, "pilot-001-region-01", [1, 1, 10, 10], [210, 260, 900, 1365]
        )
    with pytest.raises(review.ContentChanged):
        review.set_transcription(record, "working_title", "X", "Die Heimat in Amerika.")
    assert (
        record["image_description"]["working_description_de"] == "Stand aus Fenster B"
    )
    assert len(record["review_log"]) == 1


def test_decided_review_item_stays_visible_but_stops_blocking():
    src = store.object_source("pilot-001")
    working = store.new_working_copy(src)
    record = working["record"]
    findings = validate.run_all(working, src)
    imprint = next(f for f in findings if f.code == "IMPRINT_CONTEXT")
    assert imprint in validate.approval_blockers(findings)
    review.record_decision(
        record,
        imprint.code,
        imprint.message_de,
        review.decision_options(imprint.code, record)[0],
        "Aufdruck und Katalog betreffen verschiedene Kontexte.",
        "Person",
        review.decision_basis(record, imprint.code),
    )
    findings = validate.run_all(working, src)
    documented = [f for f in findings if f.category == validate.DOCUMENTED]
    assert [f.code for f in documented] == ["IMPRINT_CONTEXT"]
    assert "IMPRINT_CONTEXT" not in {
        f.code for f in validate.approval_blockers(findings)
    }
    review.set_transcription(
        record,
        "working_publisher_statement",
        "Verlag der L.P.Setzer'schen Buchhandlung in Rottweil.",
        record["transcription"]["working_publisher_statement"],
    )
    findings = validate.run_all(working, src)
    assert "IMPRINT_CONTEXT" in {f.code for f in validate.approval_blockers(findings)}


def test_required_checks_and_technical_errors_are_not_decidable():
    record = store.new_working_copy(store.object_source("pilot-001"))["record"]
    for finding in [
        validate.Finding(validate.REVIEW, "DESCRIPTION_NOT_REVIEWED", "x"),
        validate.Finding(validate.TECHNICAL, "IMPRINT_CONTEXT", "x"),
        validate.Finding(validate.NOT_RUN, "XSD_VALIDATION", "x"),
    ]:
        assert not validate.decidable(record, finding)


@pytest.mark.parametrize(
    "object_id",
    [
        "pilot-001",
        "genovefa-scan-014",
        "genovefa-scan-016",
        "genovefa-scan-017",
        "genovefa-scan-085",
    ],
)
def test_remaining_examples_validate_without_changing_fresh_state(object_id):
    sources = store.catalog()
    collection = [store.new_working_copy(src)["record"] for src in sources]
    assert {record["id"] for record in collection} == {
        "pilot-001",
        "genovefa-scan-014",
        "genovefa-scan-016",
        "genovefa-scan-017",
        "genovefa-scan-022",
        "genovefa-scan-085",
    }
    assert validate.check_duplicate_ids(collection) == []
    src = store.object_source(object_id)
    source_hash = store.sha256(src.record)
    working = store.new_working_copy(src)
    before = copy.deepcopy(working)
    findings = validate.run_all(working, src, collection)
    assert codes(findings, validate.TECHNICAL) == set()
    expected_reviews = {
        "DESCRIPTION_NOT_REVIEWED",
        "ILLUSTRATOR_ATTRIBUTION",
        "RECORD_FINAL_REVIEW",
        "REGION_NOT_REVIEWED",
    }
    expected_not_run = {"GND_LINKING", "LIVE_SOURCE", "XSD_VALIDATION"}
    if object_id == "pilot-001":
        expected_reviews |= {"IMPRINT_CONTEXT", "TRANSCRIPTION_PROVISIONAL"}
        expected_not_run.add("OCR_EVALUATION")
    else:
        expected_reviews |= {"CLASSIFICATION_DIFFERENCE", "KEYWORDS_NOT_REVIEWED"}
    assert codes(findings, validate.REVIEW) == expected_reviews
    assert codes(findings, validate.NOT_RUN) == expected_not_run
    assert "final_approval" not in working["record"]
    assert working["change_log"] == []
    assert working == before
    assert store.sha256(src.record) == source_hash
