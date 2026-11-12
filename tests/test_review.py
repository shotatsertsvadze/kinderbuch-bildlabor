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


def test_export_step_counts_as_done_only_after_final_approval():
    from kinderbuch_bildlabor import workflow

    draft = ready_record()
    assert dict(workflow.steps(draft, export_current=True))["Export"] is False
    draft["status"] = review.FINAL_APPROVED
    draft["final_approval"] = {"by": "Prüferin", "at": "2026-11-07T10:00:00+00:00"}
    assert dict(workflow.steps(draft, export_current=True))["Export"] is True
    assert workflow.next_tab(draft, export_current=True) is None


def test_reconfirming_unchanged_decision_records_new_person_and_revokes_final_approval():
    record = lead_record()
    decide(record)
    message = review.classification_message(record)
    first = dict(review.decision(record, review.CLASSIFICATION, message))
    record["final_approval"] = {"by": "Person", "at": "2026-01-01T00:00:00+00:00"}
    record["status"] = review.FINAL_APPROVED
    log_before = list(record["review_log"])
    with pytest.raises(review.DecisionInvalid):
        review.reconfirm_decision(record, review.CLASSIFICATION, message, " ", first)
    with pytest.raises(review.ContentChanged):
        stale = {**first, "rationale_de": "Andere Begründung"}
        review.reconfirm_decision(record, review.CLASSIFICATION, message, "Neu", stale)
    assert record["review_log"] == log_before and "final_approval" in record

    assert review.reconfirm_decision(
        record, review.CLASSIFICATION, message, " Neue Person ", first
    )
    entry = review.decision(record, review.CLASSIFICATION, message)
    assert entry["by"] == "Neue Person"
    assert {k: v for k, v in entry.items() if k not in ("by", "at")} == {
        k: v for k, v in first.items() if k not in ("by", "at")
    }
    assert "final_approval" not in record
    assert record["status"] != review.FINAL_APPROVED
    assert record["review_log"][: len(log_before)] == log_before
    revoked, again = record["review_log"][len(log_before) :]
    assert revoked["action"] == (
        "Endbestätigung durch erneute Bestätigung einer Entscheidung aufgehoben"
    )
    assert again["by"] == "Neue Person"
    assert again["action"].startswith("Entscheidung unverändert erneut bestätigt")


def _imported_record():
    import io

    from PIL import Image

    from kinderbuch_bildlabor import imports

    out = io.BytesIO()
    Image.new("RGB", (100, 80), "white").save(out, "PNG")
    pages = imports.preview_import([("p.png", out.getvalue())])
    return imports.imported_record("o-1", pages[0], 1, {"title": "T"})


def test_batch_region_edit_is_all_or_nothing_and_resets_only_geometry():
    record = _imported_record()
    review.add_region(record, "text", "Zeile", [10, 10, 20, 10], 1)
    first, second = (r["id"] for r in record["region_annotations"])
    review.confirm_region(record, first, "P", [0, 0, 100, 80])
    before = [r["xywh"] for r in record["region_annotations"]]
    seen = {first: before[0], second: before[1]}
    with pytest.raises(review.InvalidRegion):
        review.set_regions_xywh(
            record, {first: [0, 0, 50, 50], second: [90, 10, 20, 10]}, seen
        )
    assert [r["xywh"] for r in record["region_annotations"]] == before
    with pytest.raises(review.ContentChanged):
        review.set_regions_xywh(record, {first: [0, 0, 50, 50]}, {first: [1, 1, 1, 1]})
    assert review.set_regions_xywh(record, {first: [0, 0, 50, 50]}, seen)
    assert not review.set_regions_xywh(record, {first: [0, 0, 50, 50]}, seen)


def test_add_region_rejects_replay_and_creates_stable_transcription_field():
    record = _imported_record()
    assert review.add_region(record, "text", "Zeile", [1, 1, 5, 5], 1)
    with pytest.raises(review.ContentChanged):
        review.add_region(record, "text", "Zeile", [1, 1, 5, 5], 1)
    region = record["region_annotations"][1]
    assert region["transcription_field"] == "text_02"
    assert record["transcription"]["text_02"] == ""
    assert record["transcription"]["review_status_by_field"]["text_02"] == "provisional"


def imported_record():
    from kinderbuch_bildlabor import imports

    page = {"size": (100, 80)}
    return imports.imported_record("book-x-0001", page, 1, {"title": "Buch"})


def biblio_input(record, **changes):
    values = review.biblio_values(record)
    return {**values, **changes}, values


def test_set_biblio_changes_resets_and_noop():
    record = imported_record()
    values, seen = biblio_input(record, author=" Anna ", year="")
    assert review.set_biblio(record, values, seen)
    assert record["bibliographic_metadata_from_colibri"]["author_display"] == "Anna"
    assert record["biblio_review_status"] == review.BIBLIO_EDITED
    log_len = len(record["review_log"])
    values, seen = biblio_input(record)
    assert not review.set_biblio(record, values, seen)
    assert len(record["review_log"]) == log_len
    assert review.review_areas(record)[1]["label_de"] == "Bibliografische Angaben"
    assert not next(a for a in review.review_areas(record) if a["tab_de"] == "Angaben")[
        "done"
    ]
    review.confirm_biblio(record, "Person", seen)
    area = next(a for a in review.review_areas(record) if a["tab_de"] == "Angaben")
    assert area["done"]


def test_set_biblio_conflict_and_invalidation():
    record = imported_record()
    record["final_approval"] = {"by": "P", "at": "x"}
    record["status"] = review.FINAL_APPROVED
    values, seen = biblio_input(record, publisher="V")
    seen["publisher"] = "anders"
    with pytest.raises(review.ContentChanged):
        review.set_biblio(record, values, seen)
    assert record["bibliographic_metadata_from_colibri"]["publisher"] is None
    assert "final_approval" in record
    values, seen = biblio_input(record, publisher="V")
    review.set_biblio(record, values, seen)
    assert "final_approval" not in record


def test_set_biblio_rejects_fixture():
    record = ready_record()
    values, seen = biblio_input(record, author="X")
    with pytest.raises(review.NotAllowed):
        review.set_biblio(record, values, seen)
    assert all(a["tab_de"] != "Angaben" for a in review.review_areas(record))


def record_with_text_region():
    record = imported_record()
    review.add_region(record, "text", "Zeile", [1, 1, 20, 10], 1)
    return record


def test_withdraw_region_archives_and_keeps_ids_unique():
    record = record_with_text_region()
    text_region = record["region_annotations"][1]
    field = text_region["transcription_field"]
    record["transcription"][field] = "Hallo"
    record["ocr_candidates"] = [{"id": "c", "region_id": text_region["id"]}]
    record["final_approval"] = {"by": "P", "at": "x"}
    review.withdraw_region(
        record, text_region["id"], " Fehler ", "Person", text_region["xywh"]
    )
    assert [r["id"] for r in record["region_annotations"]] == ["book-x-0001-region-01"]
    entry = record["withdrawn_regions"][0]
    assert entry["region"]["id"] == text_region["id"]
    assert entry["transcription"]["text"] == "Hallo"
    assert entry["reason"] == "Fehler" and entry["by"] == "Person"
    assert field not in record["transcription"]
    assert field not in record["transcription"]["review_status_by_field"]
    assert record["ocr_candidates"]
    assert "final_approval" not in record
    review.add_region(record, "illustration", "Neu", [0, 0, 5, 5], 1)
    ids = [r["id"] for r in record["region_annotations"]]
    assert ids[-1] == "book-x-0001-region-03"


def test_withdraw_region_guards():
    record = imported_record()
    only = record["region_annotations"][0]
    with pytest.raises(review.NotAllowed):
        review.withdraw_region(record, only["id"], "x", "P", only["xywh"])
    record = record_with_text_region()
    second = record["region_annotations"][1]
    with pytest.raises(review.DecisionInvalid):
        review.withdraw_region(record, second["id"], " ", "P", second["xywh"])
    with pytest.raises(review.ContentChanged):
        review.withdraw_region(record, second["id"], "x", "P", [9, 9, 9, 9])
    assert len(record["region_annotations"]) == 2
    fixture = ready_record()
    first = fixture["region_annotations"][0]
    with pytest.raises(review.NotAllowed):
        review.withdraw_region(fixture, first["id"], "x", "P", first["xywh"])


def test_withdraw_decision_reopens_finding_and_archives():
    record = lead_record()
    decide(record)
    message = review.classification_message(record)
    entry = dict(review.decision(record, review.CLASSIFICATION, message))
    record["final_approval"] = {"by": "P", "at": "x"}
    record["status"] = review.FINAL_APPROVED
    with pytest.raises(review.DecisionInvalid):
        review.withdraw_decision(
            record, review.CLASSIFICATION, message, " ", "P", entry
        )
    with pytest.raises(review.ContentChanged):
        review.withdraw_decision(
            record, review.CLASSIFICATION, message, "Irrtum", "P", {**entry, "by": "X"}
        )
    assert review.decision(record, review.CLASSIFICATION, message)
    assert review.withdraw_decision(
        record, review.CLASSIFICATION, message, " Irrtum ", " Neu ", entry
    )
    assert review.decision(record, review.CLASSIFICATION, message) is None
    assert review.classification_status(record, message) == review.CLASSIFICATION_OPEN
    archived = record["withdrawn_decisions"][0]
    assert archived["decision"] == entry
    assert archived["reason"] == "Irrtum" and archived["withdrawn_by"] == "Neu"
    assert "final_approval" not in record
    last = record["review_log"][-1]
    assert last["by"] == "Neu" and "zurückgezogen" in last["action"]
    assert any("Entscheidung:" in e["action"] for e in record["review_log"])
