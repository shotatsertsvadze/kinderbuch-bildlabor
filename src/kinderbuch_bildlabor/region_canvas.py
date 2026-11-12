"""Zeichenfläche für Regionen: lokale SVG-Komponente (kein CDN), Koordinaten in Originalpixeln."""

import base64
import io
from pathlib import Path

import streamlit as st
from PIL import Image

from kinderbuch_bildlabor import regions

PREVIEW_EDGE = 2400
COMPONENT = st.components.v2.component(
    "bildlabor_region_canvas",
    html="<div></div>",
    js=Path(__file__).with_name("region_canvas.js").read_text(encoding="utf-8"),
)


@st.cache_resource(max_entries=16)
def image_data_url(path) -> str:
    image = Image.open(path).convert("RGB")
    image.thumbnail((PREVIEW_EDGE, PREVIEW_EDGE))
    output = io.BytesIO()
    image.save(output, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode()


def to_int(value) -> int:
    # Die Komponente liefert JSON-Zahlen; ganzzahlige Gleitkommawerte sind erlaubt
    if type(value) is int:
        return value
    if type(value) is float and value.is_integer():
        return int(value)
    raise ValueError("Koordinaten müssen ganze Pixelwerte sein.")


def checked_xywh(value, width: int, height: int) -> list[int]:
    if not isinstance(value, list | tuple):
        raise ValueError("Koordinaten müssen eine Liste aus vier Werten sein.")
    xywh = [to_int(v) for v in value]
    if problems := regions.bounds_problems(xywh, width, height):
        raise ValueError(" ".join(problems))
    return xywh


def normalize_event(event, known: set[str], width: int, height: int) -> dict:
    """Prüft ein Ereignis der Komponente auf dem Server; wirft ValueError bei ungültiger Geometrie."""
    if not isinstance(event, dict) or not isinstance(event.get("seq"), str):
        raise ValueError("Ungültiges Ereignis der Zeichenfläche.")
    changes = {}
    for item in event.get("changes") or []:
        if item.get("id") not in known:
            raise ValueError("Unbekannte Region im Ereignis der Zeichenfläche.")
        changes[item["id"]] = checked_xywh(item.get("xywh"), width, height)
    created = event.get("created")
    if created is not None:
        if created.get("type") not in ("illustration", "text"):
            raise ValueError("Unbekannter Regionstyp.")
        created = {
            "type": created["type"],
            "xywh": checked_xywh(created.get("xywh"), width, height),
        }
    return {"seq": event["seq"], "changes": changes, "created": created}


def pending_event(
    instance: str, known: set[str], width: int, height: int
) -> dict | None:
    """Das zuletzt gemeldete Ereignis der Fläche, geprüft; vor dem Aufbau der Anzeige zu lesen, damit sie nie einen älteren Stand erhält."""
    state = st.session_state.get(instance)
    event = state.get("edit") if state else None
    if event is None:
        return None
    return normalize_event(event, known, width, height)


def render(
    instance: str,
    image_path,
    size: tuple[int, int],
    shown: list[dict],
    created: dict | None,
) -> None:
    """Zeigt die Fläche; `shown` trägt je Region id, label, type, saved und aktuelles xywh."""
    COMPONENT(
        key=instance,
        data={
            "instance": instance,
            "image": image_data_url(str(image_path)),
            "width": size[0],
            "height": size[1],
            "regions": shown,
            "colors": {**regions.TYPE_COLORS, "other": regions.OTHER_COLOR},
            "created": created,
        },
        default={"edit": None},
        on_edit_change=lambda: None,
    )
