import copy

import pytest

from kinderbuch_bildlabor import review, store, ui, validate


def ready_record():
    record = store.new_working_copy(store.object_source("pilot-001"))["record"]
    record["review_items"] = []
    record["image_description"]["review_status"] = review.DESCRIPTION_REVIEWED
    for region in record["region_annotations"]:
        region["review_status"] = review.REGION_REVIEWED
        if "keywords_de" in region:
            region["keyword_review_status"] = review.KEYWORDS_ACCEPTED
    for field in record["transcription"]["review_status_by_field"]:
        record["transcription"]["review_status_by_field"][field] = (
            review.TRANSCRIPTION_REVIEWED
        )
    return record


def test_explicit_approval_and_invalidation():
    record = ready_record()
    assert review.readiness(record, []) == "Bereit zur Endbestätigung"
    for name, ack in [(" ", True), ("Person", False)]:
        with pytest.raises(review.ApprovalBlocked):
            review.approve_final(record, copy.deepcopy(record), name, ack, [])
    seen = copy.deepcopy(record)
    assert review.approve_final(record, seen, "Person", True, [])
    assert review.readiness(record, []) == "Endbestätigt"
    text = record["image_description"]["working_description_de"]
    assert not review.set_description(record, text, text)
    assert record["final_approval"]["by"] == "Person"
    review.set_description(record, text + " Neu", text)
    assert "final_approval" not in record
    assert review.last_confirmation(record, "final_review")["by"] == "Person"
    assert record["status"] == "draft_pending_final_review"


def test_blockers_and_stale_record():
    record = ready_record()
    for category in [validate.TECHNICAL, validate.REVIEW]:
        with pytest.raises(review.ApprovalBlocked):
            review.approve_final(
                record,
                copy.deepcopy(record),
                "Person",
                True,
                [validate.Finding(category, "BLOCK", "offen")],
            )
    with pytest.raises(review.ContentChanged):
        review.approve_final(record, {}, "Person", True, [])
    findings = [
        validate.Finding(validate.NOT_RUN, "OPTIONAL", "offen"),
        validate.Finding(validate.REVIEW, "RECORD_FINAL_REVIEW", "offen"),
    ]
    assert validate.approval_blockers(findings) == []
    assert review.approve_final(record, copy.deepcopy(record), "Person", True, findings)


def test_next_step_points_to_final_confirmation_and_then_reports_it():
    record = ready_record()
    before = ui.next_step(record, True)
    assert "Endbestätigung" in before and "nicht vorgesehen" not in before
    review.approve_final(record, copy.deepcopy(record), "Person", True, [])
    assert "endbestätigt" in ui.next_step(record, True)
    assert "Export erstellen" in ui.next_step(record, False)


def test_next_step_names_open_hints_before_final_confirmation():
    assert "Offene fachliche Hinweise (1)" in ui.next_step(ready_record(), False, 1)


LEAD = "genovefa-scan-022"


def lead_record():
    return store.new_working_copy(store.object_source(LEAD))["record"]


def decide(record, outcome_index=0, rationale="Figurenszene im Rahmen, keine Karte."):
    message = review.classification_message(record)
    options = review.decision_options(review.CLASSIFICATION, record)
    basis = review.decision_basis(record, review.CLASSIFICATION)
    return review.record_decision(
        record,
        review.CLASSIFICATION,
        message,
        options[outcome_index],
        rationale,
        "Person",
        basis,
    )


def test_decision_requires_name_listed_option_and_rationale():
    record = lead_record()
    message = review.classification_message(record)
    basis = review.decision_basis(record, review.CLASSIFICATION)
    option = review.decision_options(review.CLASSIFICATION, record)[0]
    for outcome, rationale, by in [
        (option, "Grund", " "),
        ("Erfunden", "Grund", "Person"),
        (option, "  ", "Person"),
    ]:
        with pytest.raises(review.DecisionInvalid):
            review.record_decision(
                record, review.CLASSIFICATION, message, outcome, rationale, by, basis
            )
    assert "decisions" not in record and "review_log" not in record


def test_classification_decision_closes_area_and_region_edit_revokes_it():
    record = lead_record()
    assert review.classification_labels(record) == ("Abbildung", "Karte")
    area = next(
        a for a in review.review_areas(record) if a["tab_de"] == "Klassifikation"
    )
    assert not area["done"]
    assert decide(record)
    assert not decide(record)
    area = next(
        a for a in review.review_areas(record) if a["tab_de"] == "Klassifikation"
    )
    assert area["done"]
    region = record["region_annotations"][0]
    assert not review.set_region_xywh(
        record, region["id"], region["xywh"], region["xywh"]
    )
    assert record["decisions"]
    moved = [region["xywh"][0] + 5, *region["xywh"][1:]]
    assert review.set_region_xywh(record, region["id"], moved, region["xywh"])
    assert record["decisions"] == {}
    assert "aufgehoben" in record["review_log"][-1]["action"]
    assert any("Begründung: Figurenszene" in e["action"] for e in record["review_log"])


def test_undecidable_keeps_area_open_and_decision_revokes_final_approval():
    record = lead_record()
    decide(record, outcome_index=3, rationale="Scan zu dunkel.")
    assert (
        review.classification_status(record, review.classification_message(record))
        == review.CLASSIFICATION_UNDECIDABLE
    )
    record["final_approval"] = {"by": "Person", "at": "2026-11-07T00:00:00+00:00"}
    record["status"] = review.FINAL_APPROVED
    decide(record, outcome_index=0)
    assert "final_approval" not in record


def test_pilot_labels_agree_and_need_no_classification_area():
    record = store.new_working_copy(store.object_source("pilot-001"))["record"]
    assert review.classification_labels(record) is None
    assert all(a["tab_de"] != "Klassifikation" for a in review.review_areas(record))
