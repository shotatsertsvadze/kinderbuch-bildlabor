import io
import json

from kinderbuch_bildlabor import authority, store


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_search_caches_under_data_dir_and_fetches_once(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    calls = []

    def fake(url, timeout):
        calls.append(url)
        body = {
            "member": [
                {
                    "id": "https://d-nb.info/gnd/1",
                    "preferredName": "Grimm",
                    "type": ["Person"],
                }
            ]
        }
        return Reply(json.dumps(body).encode())

    monkeypatch.setattr(authority.urllib.request, "urlopen", fake)
    first = authority.search("Grimm")
    assert first == [
        {"name": "Grimm", "uri": "https://d-nb.info/gnd/1", "type": "Person"}
    ]
    assert authority.search("Grimm") == first
    assert len(calls) == 1 and "format=json" in calls[0]
    assert list((tmp_path / "authority").glob("*.json"))


def test_empty_query_does_no_request(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("network")

    monkeypatch.setattr(authority.urllib.request, "urlopen", boom)
    assert authority.search("  ") == []
