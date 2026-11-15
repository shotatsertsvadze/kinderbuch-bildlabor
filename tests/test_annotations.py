import json

from kinderbuch_bildlabor import annotations, export, review, store


def page(record):
    return annotations.annotation_page(record, "2026-11-13T00:00:00+00:00")


def test_selector_and_target_match_region():
    record = store.new_working_copy(store.object_source("pilot-001"))["record"]
    result = page(record)
    assert result["type"] == "AnnotationPage"
    assert len(result["items"]) == len(record["region_annotations"])
    for item, region in zip(result["items"], record["region_annotations"]):
        x, y, w, h = region["xywh"]
        assert item["target"]["selector"]["type"] == "FragmentSelector"
        assert item["target"]["selector"]["value"] == f"xywh={x},{y},{w},{h}"
        assert not item["target"]["source"].endswith("info.json")


def test_draft_and_confirmed_are_labeled():
    record = store.new_working_copy(store.object_source("pilot-001"))["record"]
    region = record["region_annotations"][1]
    assert page(record)["items"][1]["bl:status"] == "draft"
    review.confirm_region(record, region["id"], "Prüfer", region["xywh"])
    item = page(record)["items"][1]
    assert item["bl:status"] == "confirmed"
    assert item["bl:region_confirmed_by"] == "Prüfer"
    purposes = {b["purpose"]: b for b in item["body"]}
    assert purposes["supplementing"]["bl:status"] == "draft"
    assert "Ground Truth" in purposes["supplementing"]["bl:note"]


def test_serialization_leaves_record_and_json_export_unchanged(tmp_path):
    working = store.new_working_copy(store.object_source("pilot-001"))
    before = json.dumps(working["record"], sort_keys=True)
    page(working["record"])
    assert json.dumps(working["record"], sort_keys=True) == before
    export.export_json(working, tmp_path / "a.json")
    assert store.read_json(tmp_path / "a.json")["record"] == working["record"]


def test_description_body_only_once_with_several_illustrations():
    record = store.new_working_copy(store.object_source("pilot-001"))["record"]
    illustration = next(
        r for r in record["region_annotations"] if r["region_type"] == "illustration"
    )
    for n in (2, 3):
        record["region_annotations"].append(
            {**illustration, "id": f"{illustration['id']}-{n}"}
        )
    items = page(record)["items"]
    described = [
        i["id"] for i in items if any(b["purpose"] == "describing" for b in i["body"])
    ]
    assert len(items) == len(record["region_annotations"])
    assert described == [f"urn:bildlabor:{illustration['id']}"]


def test_context_defines_bl_prefix():
    record = store.new_working_copy(store.object_source("pilot-001"))["record"]
    assert {"bl": annotations.BL} in page(record)["@context"]


def test_motivation_includes_commenting_for_mirador():
    record = store.new_working_copy(store.object_source("pilot-001"))["record"]
    assert all("commenting" in i["motivation"] for i in page(record)["items"])


def test_pagexml_coords_match_regions_and_flag_drafts():
    import copy
    import xml.etree.ElementTree as ET
    from pathlib import Path

    from kinderbuch_bildlabor import pagexml

    record = json.loads(Path("sammlung/genovefa/scan_022.json").read_text("utf-8"))
    before = copy.deepcopy(record)
    record["transcription"] = {
        "titel": "Thür <&>",
        "review_status_by_field": {"titel": "unreviewed"},
    }
    record["region_annotations"][0]["transcription_field"] = "titel"
    before = copy.deepcopy(record)
    root = ET.fromstring(pagexml.page_xml(record, "2026-01-01T00:00:00Z"))
    ns = {"p": pagexml.NS}
    region = record["region_annotations"][0]
    x, y, w, h = region["xywh"]
    coords = root.find(".//p:Coords", ns).get("points")
    assert coords.startswith(f"{x},{y} {x + w},{y} ")
    assert root.find(".//p:Unicode", ns).text == "Thür <&>"
    assert root.find(".//p:TextEquiv", ns).get("custom") == "status:draft"
    assert record == before


def test_report_escapes_text_and_states_caveat():
    from pathlib import Path

    from PIL import Image

    from kinderbuch_bildlabor import report

    record = json.loads(Path("sammlung/genovefa/scan_022.json").read_text("utf-8"))
    record["image_description"]["working_description_de"] = "<script>x</script>"
    record["decisions"] = {
        "k": {"outcome_de": "Ja", "rationale_de": "Grund & so", "by": "P", "at": "t"}
    }
    html = report.build(record, Image.new("RGB", (2000, 3000)), "stale")
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "Grund &amp; so" in html and "Keine Ground Truth" in html
    assert "Export veraltet" in html
