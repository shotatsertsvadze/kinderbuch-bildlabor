"""Kinderbuch-Bildlabor: Erschließung und Prüfung historischer Kinderbuch-Illustrationen.

Start: uv run streamlit run app.py
Arbeitet nur mit den gespeicherten Quelldateien; kein Netzabruf, keine OCR.
"""

import json
from collections.abc import Callable
from pathlib import Path

import streamlit as st

from kinderbuch_bildlabor import (
    check_view,
    collection_view,
    decision_view,
    library_view,
    object_view,
    review,
    store,
    ui,
    validate,
    workflow,
)

st.set_page_config(
    page_title="Kinderbuch-Bildlabor", page_icon=":material/menu_book:", layout="wide"
)
st.html(Path(workflow.__file__).with_name("workflow.css"))

COLLECTION = "sammlung"


# Bei jedem Lauf frisch von der Platte: ein anderes Fenster kann inzwischen gespeichert haben
def load_collection() -> list[ui.Current]:
    loaded = []
    for src in store.catalog():
        try:
            loaded.append(ui.Current(src, store.load_working_copy(src)))
        except json.JSONDecodeError:
            path = store.work_path(src.id).relative_to(store.DATA_DIR)
            st.error(
                f"Die Arbeitskopie {path} ist beschädigt und kann nicht gelesen werden. Die Datei wurde "
                "nicht verändert. Bitte zuerst eine Kopie der Datei an einen sicheren Ort legen und "
                "den Ordner .history neben ihr nach früheren Ständen durchsehen (er kann fehlen). "
                "Erst danach die Datei ersetzen; ohne sie beginnt das Objekt neu aus der Quelle.",
                icon=ui.ERROR,
            )
            st.stop()
    return loaded


collection = load_collection()
by_id = {cur.id: cur for cur in collection}


def view_label(view: str) -> str:
    if view == COLLECTION:
        return "Start und Sammlung"
    return f"{list(by_id).index(view) + 1} · {ui.object_label(by_id[view].record)}"


def sidebar() -> str:
    st.sidebar.markdown("### Kinderbuch-Bildlabor")
    view = st.sidebar.radio(
        "Ansicht", [COLLECTION, *by_id], format_func=view_label, key="view"
    )
    if view == COLLECTION:
        with st.sidebar:
            ui.reviewer_input()
    else:
        working = by_id[view].working
        if working["change_log"]:
            st.sidebar.caption(
                f"Zuletzt gespeichert: {ui.local_time(working['change_log'][-1]['saved_at'])}"
            )
        else:
            st.sidebar.caption(
                "Noch nichts gespeichert; angezeigt wird die unveränderte Quelldatei."
            )
    st.sidebar.caption(
        "Eingaben werden erst mit „Speichern“ übernommen. Gespeichertes bleibt nach einem "
        "Neustart erhalten."
    )
    return view


def object_page(cur: ui.Current) -> None:
    record = cur.record
    biblio, source = record["bibliographic_metadata_from_colibri"], record["source"]
    st.title(f"{biblio['title']} · Scan {source['scan_number']}")
    st.caption(
        f"{biblio['author_display']} · {biblio['publication_place']} {biblio['publication_date']} · "
        f"{source['institution']} · {source['ppn']}"
    )
    export_current = check_view.export_state(cur)[0] == "current"
    findings = validate.run_all(cur.working, cur.src, [x.record for x in collection])
    blockers = len(validate.approval_blockers(findings))
    tabs_key = f"{cur.id}-tabs"
    workflow.render(record, tabs_key, export_current, blockers)
    names = ["Übersicht"]
    views: list[Callable[[ui.Current], None]] = [object_view.overview_tab]
    if review.classification_labels(record):
        names.append("Klassifikation")
        views.append(decision_view.classification_tab)
    names += ["Regionen", "Beschreibung"]
    views += [object_view.region_tab, object_view.description_tab]
    if record.get("transcription"):
        names.append("Transkription")
        views.append(object_view.transcription_tab)
    names += ["Bibliotheksdaten", "Prüfung", "Export"]
    views += [
        lambda c: library_view.render(c.record, c.src),
        lambda c: check_view.validation_tab(c, [x.record for x in collection]),
        check_view.export_tab,
    ]
    # Eigener Schlüssel je Objekt: ein neu geöffnetes Objekt beginnt mit der Übersicht
    for tab, view in zip(st.tabs(names, key=tabs_key, on_change="rerun"), views):
        with tab:
            view(cur)


view = sidebar()
if notice := st.session_state.pop("notice", None):
    st.error(notice, icon=ui.ERROR)
if view == COLLECTION:
    collection_view.render(collection)
else:
    object_page(by_id[view])
if st.session_state.get("shown_view") != view:
    # Neue Ansicht beginnt oben. Ganz am Ende, damit sich die Position der Reiter nicht verschiebt
    # (sonst springt der Browser beim nächsten Lauf auf den ersten Reiter zurück).
    st.session_state.shown_view = view
    st.html(
        f"<script>/* {view} */ setTimeout(() => document.querySelector('[data-testid=\"stMain\"]')"
        "?.scrollTo(0, 0), 100);</script>",
        unsafe_allow_javascript=True,
    )
