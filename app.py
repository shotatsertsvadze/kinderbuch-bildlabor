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
    export_view,
    import_view,
    library_view,
    object_view,
    review,
    review_keys,
    store,
    ui,
    validate,
    theme,
    workflow,
)

st.set_page_config(
    page_title="Kinderbuch-Bildlabor", page_icon=":material/menu_book:", layout="wide"
)
theme.inject()
st.html(Path(workflow.__file__).with_name("workflow.css"))

COLLECTION = "sammlung"
SAVE_HELP = "Eingaben werden erst mit „Speichern“ übernommen. Gespeichertes bleibt nach einem Neustart erhalten."


# Bei jedem Lauf frisch von der Platte: ein anderes Fenster kann inzwischen gespeichert haben
def load_collection() -> list[ui.Current]:
    loaded = []
    for src in store.catalog():
        try:
            loaded.append(ui.Current(src, store.load_working_copy(src)))
        except store.ReadOnlyDemo:
            # Älteres Format bräuchte eine gespeicherte Umstellung; das darf die Demo nicht
            st.info(
                "Dieser Stand kann in der öffentlichen Demo nicht angezeigt werden. Die lokale "
                "Fassung zeigt ihn vollständig.",
                icon=ui.INFO,
            )
            st.stop()
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
    if view == "import":
        return "Eigenes Buch importieren"
    if view == COLLECTION:
        return "Start und Sammlung"
    # Kein Zustandssymbol im Etikett: Streamlit ordnet die Auswahl über den Etikettentext zu, und
    # ein Wechsel des Symbols (erste Speicherung) ließ die Ansicht auf „Start“ zurückspringen
    return (
        f"{list(by_id).index(view) + 1} · "
        f"{ui.object_label(by_id[view].record).replace('Scan ', 'Scan\u00a0')}"
    )


def sidebar() -> str:
    st.sidebar.markdown("### Kinderbuch-Bildlabor")
    words = [workflow.object_state(c.record)[2] for c in collection]
    final, in_work = words.count("endbestätigt"), words.count("in Arbeit")
    with st.sidebar.container(key="collection-progress"):
        st.caption(
            f"{len(collection)} Objekte · {in_work} in Arbeit · {final} endbestätigt"
        )
        st.html(
            workflow.segmented_bar(final, in_work, len(collection) - final - in_work)
        )
    # Import gibt es nur lokal
    pages = [] if store.DEMO else ["import"]
    view = st.sidebar.radio(
        "Ansicht",
        [COLLECTION, *pages, *by_id],
        format_func=view_label,
        captions=[
            "",
            *["" for _ in pages],
            *("{} {}".format(*workflow.object_state(c.record)[:2]) for c in collection),
        ],
        key="view",
        label_visibility="collapsed",
    )
    if view in {COLLECTION, "import"}:
        with st.sidebar:
            ui.reviewer_input()
    else:
        working = by_id[view].working
        save_help = None if store.DEMO else SAVE_HELP
        if working["change_log"]:
            st.sidebar.caption(
                f"Zuletzt gespeichert: {ui.local_time(working['change_log'][-1]['saved_at'])}",
                help=save_help,
            )
        else:
            st.sidebar.caption(
                "Angezeigt wird die unveränderte Quelldatei."
                if store.DEMO
                else "Noch nichts gespeichert; angezeigt wird die unveränderte Quelldatei.",
                help=save_help,
            )
    return view


def object_page(cur: ui.Current) -> None:
    record = cur.record
    biblio, source = record["bibliographic_metadata_from_colibri"], record["source"]
    published = (
        f"{biblio['publication_place'] or ''} {biblio['publication_date'] or ''}"
    )
    heading, reviewer = st.container(key="object-head").columns(
        [7, 2], vertical_alignment="bottom", gap="large"
    )
    with heading:
        with st.container(key="object-eyebrow"):
            st.caption(
                " · ".join(
                    p
                    for p in (
                        "SAMMLUNG",
                        biblio["title"].upper(),
                        published.strip().upper(),
                    )
                    if p
                )
            )
        # Geschütztes Leerzeichen: „Scan 22“ bricht nicht um
        st.title(f"{biblio['title']} · Scan\u00a0{source['scan_number']}")
        parts = [
            biblio["author_display"],
            published.strip(),
            source["institution"],
            f"`{source['ppn']}`" if source["ppn"] else None,
        ]
        # Trennpunkt bleibt am vorigen Teil: kein verwaister „·“ am Zeilenanfang
        with st.container(key="object-sub"):
            st.caption("\u00a0· ".join(p or "unbekannt" for p in parts))
    with reviewer, st.container(key="object-reviewer"):
        ui.reviewer_input()
    export_current = export_view.export_state(cur)[0] == "current"
    findings = validate.run_all(cur.working, cur.src, [x.record for x in collection])
    blockers = len(validate.approval_blockers(findings))
    names = ["Übersicht"]
    views: list[Callable[[ui.Current], None]] = [object_view.overview_tab]
    if review.classification_labels(record):
        names.append("Klassifikation")
        views.append(decision_view.classification_tab)
    names.append("Regionen")
    views.append(object_view.region_tab)
    if review.is_imported(record):
        names.append("Angaben")
        views.append(object_view.biblio_tab)
    names.append("Beschreibung")
    views.append(object_view.description_tab)
    if record.get("transcription"):
        names.append("Transkription")
        views.append(object_view.transcription_tab)
    names += ["Bibliotheksdaten", "Prüfung", "Export"]
    views += [
        lambda c: library_view.render(c.record, c.src),
        lambda c: check_view.validation_tab(c, [x.record for x in collection]),
        export_view.export_tab,
    ]
    tabs_key = f"{cur.id}-tabs"
    workflow.render(
        record,
        tabs_key,
        names,
        export_current,
        blockers,
        footer=lambda: review_keys.render(record, tabs_key, export_current, blockers),
    )
    # Eigener Schlüssel je Objekt: ein neu geöffnetes Objekt beginnt mit der Übersicht
    # Ändert sich die Reiterliste (neue Textregion), bleibt der gewählte Reiter erhalten
    chosen = st.session_state.get(tabs_key)
    default = chosen if chosen in names else None
    tabs = st.tabs(names, key=tabs_key, on_change="rerun", default=default)
    for tab, view in zip(tabs, views):
        with tab:
            view(cur)


view = sidebar()
if store.DEMO:
    ui.demo_notice()
if notice := st.session_state.pop("notice", None):
    with st.container(key="page-notice"):
        st.error(notice, icon=ui.ERROR)
        ui.show_notice()
if view == COLLECTION:
    collection_view.render(collection)
elif view == "import":
    import_view.render()
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
