import copy

import pytest

from kinderbuch_bildlabor import review, store, validate


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
    assert review.readiness(record, []) == "Bereit zur Endprüfung"
    for name, ack in [(" ", True), ("Person", False)]:
        with pytest.raises(review.ApprovalBlocked):
            review.approve_final(record, copy.deepcopy(record), name, ack, [])
    seen = copy.deepcopy(record)
    assert review.approve_final(record, seen, "Person", True, [])
    assert review.readiness(record, []) == "Abschließend bestätigt"
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
