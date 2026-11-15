"""Explizite GND-Suche über lobid-gnd. Nur auf Knopfdruck; Treffer sind Kandidaten, keine Verknüpfung."""

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

from kinderbuch_bildlabor import store

URL = "https://lobid.org/gnd/search"


def _cache_file(query: str) -> Path:
    digest = hashlib.sha256(query.encode()).hexdigest()[:16]
    return store.DATA_DIR / "authority" / f"{digest}.json"


def search(query: str, size: int = 5) -> list[dict]:
    """[{'name', 'uri', 'type'}]; wiederholte Anfragen kommen aus dem Zwischenspeicher im Datenordner."""
    query = query.strip()
    if not query:
        return []
    cache = _cache_file(query)
    if cache.is_file():
        return json.loads(cache.read_text("utf-8"))
    params = urllib.parse.urlencode({"q": query, "format": "json", "size": size})
    with urllib.request.urlopen(f"{URL}?{params}", timeout=20) as response:
        data = json.load(response)
    found = [
        {
            "name": item.get("preferredName", ""),
            "uri": item["id"],
            "type": ", ".join(item.get("type", [])),
        }
        for item in data.get("member", [])
    ]
    store.write_json(cache, found)
    return found
