from kinderbuch_bildlabor import store

PILOT = store.object_source("pilot-001")


def test_new_copy_references_source_and_keeps_values():
    working = store.new_working_copy(PILOT)
    assert working["based_on"]["file"] == "Kinderbuch_Bildlabor_Start/pilot_001.json"
    assert working["based_on"]["sha256"] == store.sha256(PILOT.record)
    record = working["record"]
    assert record["id"] == "pilot-001"
    assert record["image_description"]["illustrator"] is None
    assert record["source"]["printed_page_number"] is None
    assert record["ocr_result"]["raw_text"] == "‘Die Geimatly „ir Amerika.\n"


def test_saved_edit_survives_reload_and_source_stays_unchanged(tmp_path):
    source_hash = store.sha256(PILOT.record)
    working = store.load_working_copy(PILOT, work_dir=tmp_path)
    working["record"]["image_description"]["working_description_de"] = "Geänderte Beschreibung"
    store.save_working_copy(working, "Beschreibung", work_dir=tmp_path)

    reloaded = store.load_working_copy(PILOT, work_dir=tmp_path)
    assert reloaded["record"]["image_description"]["working_description_de"] == "Geänderte Beschreibung"
    assert reloaded["change_log"][-1]["area_de"] == "Beschreibung"
    assert store.sha256(PILOT.record) == source_hash


def old_format_working(status: str = "provisional") -> dict:
    """Arbeitskopie im bisherigen Format mit einem gemeinsamen Transkriptions-Prüfstand."""
    working = {"based_on": {"file": "Kinderbuch_Bildlabor_Start/pilot_001.json",
                            "sha256": store.sha256(PILOT.record)},
               "change_log": [{"saved_at": "2026-11-06T14:50:11+00:00", "area_de": "Bestätigung Region"}],
               "record": store.read_json(PILOT.record)}
    working["record"]["transcription"]["review_status"] = status
    working["record"]["review_log"] = [{"at": "2026-11-06T14:50:11+00:00", "area": "pilot-001-region-02",
                                        "action": "Regionsgrenzen visuell bestätigt", "by": "Testperson"}]
    return working


def test_migration_splits_transcription_status_per_field():
    record = old_format_working("reviewed")["record"]
    assert store.migrate_record(record) == [store.MIGRATION_SPLIT_TRANSCRIPTION, store.MIGRATION_DESCRIPTION_STATUS]
    assert "review_status" not in record["transcription"]
    assert record["transcription"]["review_status_by_field"] == {
        "working_title": "reviewed", "working_publisher_statement": "reviewed"}
    assert record["image_description"]["review_status"] == "unreviewed"
    assert store.migrate_record(record) == []


def test_new_working_copy_uses_split_status_and_leaves_source_unchanged():
    source_hash = store.sha256(PILOT.record)
    transcription = store.new_working_copy(PILOT)["record"]["transcription"]
    assert transcription["review_status_by_field"] == {
        "working_title": "provisional", "working_publisher_statement": "provisional"}
    assert store.sha256(PILOT.record) == source_hash


def test_existing_work_file_is_migrated_once_and_keeps_history(tmp_path):
    old = old_format_working()
    store.write_json(store.work_path("pilot-001", tmp_path), old)

    migrated = store.load_working_copy(PILOT, work_dir=tmp_path)
    assert [c["area_de"] for c in migrated["change_log"]] == [
        "Bestätigung Region", store.MIGRATION_SPLIT_TRANSCRIPTION, store.MIGRATION_DESCRIPTION_STATUS]
    assert migrated["record"]["review_log"] == old["record"]["review_log"]
    assert migrated["record"]["transcription"]["working_title"] == "Die Heimath in Amerika."

    again = store.load_working_copy(PILOT, work_dir=tmp_path)
    assert len(again["change_log"]) == 3


def test_simultaneous_saves_lose_no_update(tmp_path):
    """Nachweis vorher: 30 gleichzeitige Speicherungen ergaben 5 Einträge und 20 FileNotFoundError."""
    import threading
    from kinderbuch_bildlabor import review

    def change(i):
        def apply(record):
            review.log(record, f"bereich-{i}", "Test")
            return True
        return apply

    threads = [threading.Thread(target=store.update_working_copy, args=(PILOT, change(i), f"Test {i}"),
                                kwargs={"work_dir": tmp_path}) for i in range(30)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    saved = store.load_working_copy(PILOT, work_dir=tmp_path)
    assert len(saved["record"]["review_log"]) == 30
    assert len(saved["change_log"]) == 30
    assert list(tmp_path.glob("*.tmp")) == []
