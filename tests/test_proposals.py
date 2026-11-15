import io
import json

from PIL import Image

from kinderbuch_bildlabor import proposals


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_propose_clamps_box_and_sends_only_to_localhost(monkeypatch):
    seen = []

    def fake(request, timeout):
        seen.append(request.full_url)
        content = {
            "x": -5,
            "y": 10,
            "width": 500,
            "height": 20,
            "description_de": " Ein Haus ",
        }
        return Reply(json.dumps({"message": {"content": json.dumps(content)}}).encode())

    monkeypatch.setattr(proposals.urllib.request, "urlopen", fake)
    result = proposals.propose(Image.new("RGB", (100, 50)))
    assert result == {"xywh": [0, 10, 100, 20], "description_de": "Ein Haus"}
    assert seen == ["http://localhost:11434/api/chat"]


def test_unavailable_when_connection_fails(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError

    monkeypatch.setattr(proposals.urllib.request, "urlopen", fail)
    assert proposals.available() is False
