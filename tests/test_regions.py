from PIL import Image, ImageChops, ImageStat

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
