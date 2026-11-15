"""Ähnliche Illustrationen über Differenz-Hash und Farbraster (nur Pillow). Der Index liegt im Datenordner."""

from PIL import Image

from kinderbuch_bildlabor import store

GRID = 3


def features(image: Image.Image) -> dict:
    gray = image.convert("L").resize((9, 8))
    pixels = list(gray.tobytes())
    bits = [
        pixels[row * 9 + col] > pixels[row * 9 + col + 1]
        for row in range(8)
        for col in range(8)
    ]
    colours = [v / 255 for v in image.convert("RGB").resize((GRID, GRID)).tobytes()]
    return {"hash": bits, "colour": colours}


def distance(a: dict, b: dict) -> float:
    hamming = sum(x != y for x, y in zip(a["hash"], b["hash"])) / len(a["hash"])
    colour = sum(abs(x - y) for x, y in zip(a["colour"], b["colour"])) / len(
        a["colour"]
    )
    return hamming + colour


def _index_path():
    return store.DATA_DIR / "index" / "similar.json"


def load_index() -> dict:
    path = _index_path()
    return store.read_json(path) if path.is_file() else {}


def nearest(
    target: dict, entries: dict[str, dict], exclude: str, limit: int = 5
) -> list[tuple[str, float]]:
    scored = [(k, distance(target, f)) for k, f in entries.items() if k != exclude]
    return sorted(scored, key=lambda item: item[1])[:limit]


def entry_key(object_id: str, region: dict) -> str:
    return f"{object_id}|{region['id']}|{region['xywh']}"


def build(items: list[tuple[str, dict, Image.Image]]) -> dict[str, dict]:
    """items: (Objekt, Region, Seitenbild). Schreibt neue Einträge in den Index im Datenordner."""
    index = load_index()
    changed = False
    for object_id, region, page in items:
        key = entry_key(object_id, region)
        if key not in index:
            x, y, w, h = region["xywh"]
            index[key] = features(page.crop((x, y, x + w, y + h)))
            changed = True
    if changed:
        store.write_json(_index_path(), index)
    return index
