import csv

from kinderbuch_bildlabor import export, review, store


def test_json_export_roundtrip_keeps_unicode_nulls_regions_and_status(tmp_path):
    working = store.new_working_copy(store.object_source("pilot-001"))
    review.confirm_region(
        working["record"], "pilot-001-region-02", "Prüfer", [400, 1640, 550, 80]
    )
    path = tmp_path / "pilot-001.json"
    export.export_json(working, path)

    reloaded = store.read_json(path)["record"]
    report = export.roundtrip_report(working["record"], reloaded)
    assert all(ok for _, ok in report), report
    assert reloaded["ocr_result"]["raw_text"] == "‘Die Geimatly „ir Amerika.\n"
    assert reloaded["image_description"]["illustrator"] is None
    assert "‘Die Geimatly" in path.read_text(encoding="utf-8")


def test_roundtrip_report_detects_lost_null_and_changed_status():
    working = store.new_working_copy(store.object_source("pilot-001"))
    damaged = store.new_working_copy(store.object_source("pilot-001"))["record"]
    damaged["image_description"]["illustrator"] = ""
    damaged["transcription"]["review_status_by_field"]["working_title"] = "reviewed"
    report = dict(export.roundtrip_report(working["record"], damaged))
    assert report["Nullwerte bleiben null (nicht leer, nicht entfernt)"] is False
    assert report["Alle Prüfstände unverändert"] is False


def test_csv_has_one_row_per_region_with_provenance(tmp_path):
    record = store.new_working_copy(store.object_source("pilot-001"))["record"]
    path = tmp_path / "pilot-001.csv"
    export.export_csv(record, "2026-11-06T00:00:00+00:00", path)

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["region_id"] for r in rows] == [
        "pilot-001-region-01",
        "pilot-001-region-02",
        "pilot-001-region-03",
    ]
    assert rows[0]["suchbegriffe"] == "Personengruppe; Baum; Landschaft"
    assert rows[1]["transkription"] == "Die Heimath in Amerika."
    assert rows[1]["transkription_pruefstatus"] == "provisional"
    assert rows[0]["illustrator"] == ""
    assert all(
        r["colibri_lizenz"] == "https://creativecommons.org/licenses/by/4.0/"
        for r in rows
    )
    assert all(r["rechte_quellwerk"] == "Public Domain Mark 1.0" for r in rows)


def export_then_confirm(tmp_path):
    """Nachgestellter Ablauf: exportieren, danach eine Bestätigung speichern."""
    working = store.load_working_copy(
        store.object_source("pilot-001"), work_dir=tmp_path / "work"
    )
    exported = export.export_json(working, tmp_path / "pilot-001.json")
    review.confirm_region(
        working["record"], "pilot-001-region-02", "Testperson", [400, 1640, 550, 80]
    )
    store.save_working_copy(
        working,
        "Bestätigung Regionsgrenzen pilot-001-region-02",
        work_dir=tmp_path / "work",
    )
    return working, store.read_json(tmp_path / "pilot-001.json"), exported


def test_export_followed_by_confirmation_is_reported_as_stale(tmp_path):
    working, reloaded, _ = export_then_confirm(tmp_path)
    later = export.later_changes(working, reloaded)
    assert [c["area_de"] for c in later] == [
        "Bestätigung Regionsgrenzen pilot-001-region-02"
    ]


def test_new_export_after_confirmation_is_current_and_faithful(tmp_path):
    working, _, _ = export_then_confirm(tmp_path)
    export.export_json(working, tmp_path / "pilot-001.json")
    reloaded = store.read_json(tmp_path / "pilot-001.json")
    assert export.later_changes(working, reloaded) == []
    assert all(
        ok for _, ok in export.roundtrip_report(working["record"], reloaded["record"])
    )


def test_export_from_other_history_is_not_treated_as_current(tmp_path):
    working, reloaded, _ = export_then_confirm(tmp_path)
    reloaded["change_log"] = [
        {"saved_at": "2026-01-01T00:00:00+00:00", "area_de": "fremd"}
    ]
    assert export.later_changes(working, reloaded) is None


def test_added_text_with_umlaut_is_not_reported_as_unicode_problem():
    original = store.new_working_copy(store.object_source("pilot-001"))["record"]
    reloaded = store.new_working_copy(store.object_source("pilot-001"))["record"]
    review.confirm_region(
        original, "pilot-001-region-02", "Testperson", [400, 1640, 550, 80]
    )
    report = dict(export.roundtrip_report(original, reloaded))
    assert report["Unicode-Texte unverändert (z. B. ‘ „ ä ß ×)"] is True
    assert report["Gesamter Datensatz identisch"] is False


def test_changed_unicode_text_is_still_detected():
    original = store.new_working_copy(store.object_source("pilot-001"))["record"]
    damaged = store.new_working_copy(store.object_source("pilot-001"))["record"]
    damaged["ocr_result"]["raw_text"] = '"Die Geimatly "ir Amerika.\n'
    report = dict(export.roundtrip_report(original, damaged))
    assert report["Unicode-Texte unverändert (z. B. ‘ „ ä ß ×)"] is False


def test_differing_fields_names_the_changed_field():
    original = store.new_working_copy(store.object_source("pilot-001"))["record"]
    reloaded = store.new_working_copy(store.object_source("pilot-001"))["record"]
    assert export.differing_fields(original, reloaded) == []
    reloaded["transcription"]["working_publisher_statement"] = (
        "Verlag der I.P.Setzer'schen Buchhandlung in Rottweil"
    )
    reloaded["image_description"]["illustrator"] = ""
    assert export.differing_fields(original, reloaded) == [
        "image_description › illustrator",
        "transcription › working_publisher_statement",
    ]


def test_final_approval_export_and_status_readback(tmp_path):
    import copy
    from test_review import ready_record

    working = store.new_working_copy(store.object_source("pilot-001"))
    record = ready_record()
    working["record"] = record
    review.approve_final(record, copy.deepcopy(record), "Endprüfer", True, [])
    path = tmp_path / "approved.json"
    export.export_json(working, path)
    reloaded = store.read_json(path)["record"]
    assert reloaded["review_log"] == record["review_log"]
    assert all(ok for _, ok in export.roundtrip_report(record, reloaded))
    row = export.csv_rows(record, "jetzt")[0]
    assert row["endpruefung_person"] == "Endprüfer"
    assert row["endpruefung_am"] == record["final_approval"]["at"]
    reloaded["status"] = "draft_pending_final_review"
    assert not dict(export.roundtrip_report(record, reloaded))[
        "Alle Prüfstände unverändert"
    ]


def test_csv_neutralizes_formula_prefixes_without_changing_rows(tmp_path):
    texts = [
        "=Text",
        "+Text",
        "-Text",
        "@Text",
        "\tText",
        "\rText",
        "\nText",
        "  =Text",
        "\t+Text",
        "\r\n@Text",
    ]
    rows = [{"beschreibung": text, "x": -1} for text in texts]
    path = tmp_path / "text.csv"
    export.write_csv(rows, path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        saved = list(csv.DictReader(handle))
    assert [row["beschreibung"] for row in saved] == ["'" + text for text in texts]
    assert [row["x"] for row in saved] == ["-1"] * len(texts)
    assert rows == [{"beschreibung": text, "x": -1} for text in texts]


def test_csv_keeps_ordinary_text_unchanged(tmp_path):
    texts = [
        "",
        "Text mit ä und ß",
        "Ein - Zeichen",
        "'Text",
        "  Text",
        'Text, "Zitat"\nZeile',
    ]
    path = tmp_path / "ordinary.csv"
    export.write_csv([{"beschreibung": text} for text in texts], path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        assert [row["beschreibung"] for row in csv.DictReader(handle)] == texts


def test_both_csv_exports_neutralize_text_and_json_keeps_originals(tmp_path):
    import copy

    working = store.new_working_copy(store.object_source("pilot-001"))
    record = working["record"]
    record["image_description"]["working_description_de"] = "=Text"
    record["transcription"]["working_title"] = "+Text"
    record["final_approval"] = {"by": "@Text", "at": "jetzt"}
    before = copy.deepcopy(working)
    for filename, write in [
        ("object.csv", lambda path: export.export_csv(record, "jetzt", path)),
        (
            "collection.csv",
            lambda path: export.export_collection_csv([record], "jetzt", path),
        ),
    ]:
        path = tmp_path / filename
        write(path)
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows[0]["beschreibung"] == "'=Text"
        assert rows[1]["transkription"] == "'+Text"
        assert all(row["endpruefung_person"] == "'@Text" for row in rows)
    export.export_json(working, tmp_path / "original.json")
    assert store.read_json(tmp_path / "original.json")["record"] == before["record"]
    assert working == before
