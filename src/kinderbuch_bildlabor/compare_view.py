"""Zwei Objekte nebeneinander. Nur Anzeige: nichts wird gespeichert, nichts normalisiert."""

import streamlit as st

from kinderbuch_bildlabor import regions, review, ui


def rows(a: dict, b: dict) -> list[dict]:
    """Buchangaben und Transkriptionen im Vergleich; Abweichung heißt buchstäblich verschieden."""
    result = []
    for label, section, key in review.BIBLIO_FIELDS.values():
        va, vb = a[section][key], b[section][key]
        result.append(_row(label, va, vb))
    ta, tb = a.get("transcription") or {}, b.get("transcription") or {}
    for key in sorted(set(ta) | set(tb)):
        if key != "review_status_by_field" and not isinstance(
            ta.get(key, tb.get(key)), dict
        ):
            result.append(_row(f"Transkription {key}", ta.get(key), tb.get(key)))
    return result


def _row(label: str, va, vb) -> dict:
    return {
        "Feld": label,
        "Objekt A": "" if va is None else str(va),
        "Objekt B": "" if vb is None else str(vb),
        "Vergleich": "gleich" if va == vb else "abweichend",
    }


def render(collection: list[ui.Current]) -> None:
    ui.section("Zwei Objekte vergleichen")
    if len(collection) < 2:
        return
    ids = [cur.id for cur in collection]
    by_id = {cur.id: cur for cur in collection}
    left, right = st.columns(2)
    first = left.selectbox("Objekt A", ids, index=0, key="compare-a")
    second = right.selectbox("Objekt B", ids, index=1, key="compare-b")
    for column, object_id in ((left, first), (right, second)):
        cur = by_id[object_id]
        region = cur.record["region_annotations"][0]
        column.image(
            regions.crop(ui.page_image(cur.src.page_image), region["xywh"]),
            caption=f"{object_id}: erste Region",
        )
    st.dataframe(
        rows(by_id[first].record, by_id[second].record),
        hide_index=True,
        key="compare-table",
    )
    st.caption(
        "Buchstäblicher Vergleich ohne Normalisierung; Abweichungen sind Befunde, keine Fehler."
    )
