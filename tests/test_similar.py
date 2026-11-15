from PIL import Image

from kinderbuch_bildlabor import similar, store


def gradient(flip=False):
    image = Image.new("RGB", (40, 40))
    image.putdata(
        [
            ((x if not flip else 39 - x) * 6, 10, 10)
            for y in range(40)
            for x in range(40)
        ]
    )
    return image


def test_identical_ranks_first_and_index_stays_in_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    region = {"id": "r", "xywh": [0, 0, 40, 40]}
    items = [
        ("a", region, gradient()),
        ("b", region, gradient()),
        ("c", region, gradient(flip=True)),
    ]
    index = similar.build(items)
    ranked = similar.nearest(
        index[similar.entry_key("a", region)], index, similar.entry_key("a", region)
    )
    assert ranked[0][0].startswith("b|") and ranked[0][1] == 0
    assert ranked[0][1] < ranked[1][1]
    assert [
        p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()
    ] == ["index/similar.json"]
