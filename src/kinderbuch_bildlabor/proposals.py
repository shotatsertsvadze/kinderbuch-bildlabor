"""Vorschläge eines lokalen Ollama-Modells (nur localhost, nur auf Knopfdruck). Ergebnis ist ein ungeprüfter Entwurf."""

import base64
import io
import json
import os
import urllib.request

from PIL import Image

from kinderbuch_bildlabor import store

HOST = "http://localhost:11434"
SCHEMA = {
    "type": "object",
    "properties": {
        "x": {"type": "integer"},
        "y": {"type": "integer"},
        "width": {"type": "integer"},
        "height": {"type": "integer"},
        "description_de": {"type": "string"},
    },
    "required": ["x", "y", "width", "height", "description_de"],
}
PROMPT = (
    "Dies ist die Seite eines historischen Kinderbuchs. Gib den Rahmen der Illustration in Pixeln "
    "(x, y, width, height ab der linken oberen Ecke dieses Bildes) und eine sachliche deutsche "
    "Beschreibung dessen an, was zu sehen ist."
)


def model() -> str:
    return os.environ.get("BILDLABOR_OLLAMA_MODEL", "qwen2.5vl")


def available() -> bool:
    if store.DEMO:
        return False
    try:
        with urllib.request.urlopen(f"{HOST}/api/tags", timeout=0.5):
            return True
    except OSError:
        return False


def propose(image: Image.Image) -> dict:
    """{'xywh': [x, y, w, h] innerhalb des Bildes, 'description_de': str}."""
    store.refuse_in_demo("Modellvorschlag")
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, "JPEG")
    body = {
        "model": model(),
        "stream": False,
        "format": SCHEMA,
        "messages": [
            {
                "role": "user",
                "content": PROMPT,
                "images": [base64.b64encode(buffer.getvalue()).decode()],
            }
        ],
    }
    request = urllib.request.Request(
        f"{HOST}/api/chat",
        json.dumps(body).encode(),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        answer = json.load(response)["message"]["content"]
    data = json.loads(answer)
    width, height = image.size
    x = min(max(data["x"], 0), width - 1)
    y = min(max(data["y"], 0), height - 1)
    w = min(max(data["width"], 1), width - x)
    h = min(max(data["height"], 1), height - y)
    return {"xywh": [x, y, w, h], "description_de": data["description_de"].strip()}
