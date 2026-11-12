from PIL import Image, ImageChops, ImageColor, ImageStat

from kinderbuch_bildlabor import regions, store

WIDTH, HEIGHT = 1183, 1950


def mean_difference(a: Image.Image, b: Image.Image) -> float:
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3


def test_pilot_regions_are_inside_image():
    record = store.read_json(store.object_source("pilot-001").record)
    for region in record["region_annotations"]:
        assert regions.bounds_problems(region["xywh"], WIDTH, HEIGHT) == []


def test_invalid_bounds_are_reported():
    assert regions.bounds_problems([1100, 0, 100, 10], WIDTH, HEIGHT)
    assert regions.bounds_problems([0, 0, 0, 10], WIDTH, HEIGHT)
    assert regions.bounds_problems([-1, 0, 10, 10], WIDTH, HEIGHT)
    assert regions.bounds_problems([0, 0, 10], WIDTH, HEIGHT)
    assert regions.bounds_problems([0, 0, 10.5, 10], WIDTH, HEIGHT)
    assert regions.bounds_problems([1083, 1850, 100, 100], WIDTH, HEIGHT) == []


def test_title_crop_matches_iiif_crop_of_same_region():
    """Der lokale Ausschnitt muss dem unveränderten IIIF-Ausschnitt entsprechen.

    Gemessen: Abweichung 1,12 ohne Versatz, ab 4,39 bei 1 Pixel Versatz (JPEG-Rauschen).
    """
    page = Image.open(store.object_source("pilot-001").page_image).convert("RGB")
    reference = Image.open(store.SOURCE_DIR / "pilot_001_title.jpg").convert("RGB")
    title = regions.crop(page, [400, 1640, 550, 80])
    shifted = regions.crop(page, [401, 1640, 550, 80])
    assert title.size == reference.size == (550, 80)
    assert mean_difference(title, reference) < 2.5
    assert mean_difference(shifted, reference) > 2.5


def test_drawing_keeps_original_size():
    page = Image.open(store.object_source("pilot-001").page_image)
    record = store.read_json(store.object_source("pilot-001").record)
    marked = regions.draw_regions(page, record["region_annotations"])
    assert marked.size == (WIDTH, HEIGHT)


def test_region_frame_has_light_and_dark_edges_on_any_paper():
    page = Image.new("RGB", (400, 400), (181, 160, 134))
    marked = regions.draw_regions(
        page, [{"xywh": [100, 100, 200, 200], "region_type": "illustration"}]
    )
    assert marked.getpixel((98, 200)) == (255, 255, 255)
    assert marked.getpixel((103, 200)) == ImageColor.getrgb(
        regions.TYPE_COLORS["illustration"]
    )
    assert marked.getpixel((107, 200)) == (0, 0, 0)


def test_canvas_event_accepts_whole_floats_and_rejects_invalid_geometry():
    import pytest

    from kinderbuch_bildlabor import region_canvas

    event = {
        "seq": "a",
        "changes": [{"id": "r", "xywh": [1.0, 2, 3, 4]}],
        "created": None,
    }
    assert region_canvas.normalize_event(event, {"r"}, 10, 10)["changes"] == {
        "r": [1, 2, 3, 4]
    }
    for bad in ([1.5, 0, 2, 2], [0, 0, 20, 2], [0, 0, 0, 2]):
        event["changes"][0]["xywh"] = bad
        with pytest.raises(ValueError):
            region_canvas.normalize_event(event, {"r"}, 10, 10)
    event["changes"][0] = {"id": "x", "xywh": [0, 0, 1, 1]}
    with pytest.raises(ValueError):
        region_canvas.normalize_event(event, {"r"}, 10, 10)
