"""Startseite: Leitfrage, Fallstudie, Einstieg, Begriffe und die Objekte der Sammlung."""

import os
from pathlib import Path

import streamlit as st
from PIL import Image

from kinderbuch_bildlabor import (
    actions,
    agreement,
    backup_view,
    colibri,
    colibri_sample,
    compare_view,
    example_view,
    matrix,
    regions,
    review,
    search,
    store,
    triage,
    ui,
    validate,
    workflow,
)

QUESTION = (
    "Wie lassen sich abweichende Bildklassifikationen in digitalisierten Kinderbüchern am "
    "Originalbild prüfen, begründet entscheiden und mit ihrer Herkunft weitergeben?"
)
LEAD = "genovefa-scan-022"
SECOND = "pilot-001"
TERMS = [
    (
        "Prüfbereich",
        "eine einzeln bestätigte Einheit: Regionsgrenzen, Klassifikation, Beschreibung, "
        "Suchbegriffe, jede Transkription. Eine spätere Änderung setzt nur diesen Bereich zurück.",
    ),
    (
        "Begründete Entscheidung",
        "Festlegung einer benannten Person zu einem belegten Unterschied, zum Beispiel zwei "
        "abweichenden Klassen, mit Begründung. Beide Ausgangswerte bleiben erhalten.",
    ),
    (
        "Endbestätigung",
        "eine benannte Person hat den gesamten gespeicherten Arbeitsstand eines Objekts "
        "durchgesehen. Möglich erst, wenn alle Prüfbereiche bestätigt und keine Blocker offen sind.",
    ),
    (
        "Ground Truth",
        "eine geprüfte Referenz, an der automatische Verfahren gemessen werden. Wird hier nicht "
        "vergeben, auch nicht durch die Endbestätigung; dafür fehlt eine unabhängige Zweitprüfung.",
    ),
]


@st.cache_resource(max_entries=64)
def thumbnail(path, xywh: tuple[int, ...]) -> Image.Image:
    image = regions.crop(ui.page_image(path), list(xywh))
    image.thumbnail((420, 300))
    return image


def render(collection: list[ui.Current]) -> None:
    by_id = {cur.id: cur for cur in collection}
    hero(by_id[LEAD])
    books = {
        cur.record["source"]["ppn"] or cur.record["metadata_provenance"]["title"]
        for cur in collection
    }
    ui.section(f"Stichprobe: {len(collection)} Illustrationen aus {len(books)} Büchern")
    columns = st.columns(3)
    records = [cur.record for cur in collection]
    for index, cur in enumerate(collection):
        with columns[index % 3], st.container(border=True, key=f"card-{cur.id}"):
            card(cur, records)
    queue(collection)
    agreement_panel(collection)
    search_panel(collection)
    compare_view.render(collection)
    class_matrix(collection)
    case_study(collection)
    example_view.render()
    second_example(by_id[SECOND].record)
    glossary()
    export_column, backup_column = st.columns(2, gap="large")
    with export_column, st.container(border=True):
        collection_export(collection)
    with backup_column, st.container(border=True):
        backup_view.render()


def queue(collection: list[ui.Current]) -> None:
    ui.section("Warteschlange: was zuerst geprüft werden sollte")
    st.caption(
        "Reihenfolge: offene Klassenabweichung, dann die meisten offenen Blocker, dann die "
        "wenigsten bestätigten Bereiche; endbestätigte Objekte zuletzt."
    )
    by_id = {cur.id: cur for cur in collection}
    for number, item in enumerate(triage.rank(collection), start=1):
        with st.container(border=True, horizontal=True, key=f"queue-{item.id}"):
            st.markdown(
                f"**{number}. {item.title}** ({by_id[item.id].record['source']['scan_number']})  \n"
                f"{'Klassenabweichung offen · ' if item.disagreement else ''}"
                f"{item.blockers} Blocker · {item.confirmed} von {item.total} Bereichen bestätigt"
                f"{' · endbestätigt' if item.approved else ''}"
            )
            st.button(
                "Öffnen",
                key=f"queue-open-{item.id}",
                on_click=actions.open_object,
                args=(item.id,),
            )


def agreement_panel(collection: list[ui.Current]) -> None:
    ui.section("Übereinstimmung von Erst- und Zweitprüfung")
    result = agreement.collect({cur.id: cur.record for cur in collection})
    st.caption(
        "Konventionsstatistik nach selbst angegebenen Namen, keine Ground Truth. "
        "Gezählt werden nur gültige Zweitprüfungen; die Endbestätigung gilt als Zustimmung der ersten Person."
    )
    if not result["per_area"]:
        st.info("Noch keine gültige Zweitprüfung vorhanden.")
        return
    st.dataframe(
        [
            {"Bereich": k, "Zustimmung": c["agree"], "Abweichung": c["disagree"]}
            for k, c in sorted(result["per_area"].items())
        ],
        hide_index=True,
        key="agreement-table",
    )
    kappa = result["kappa"]
    st.caption(
        "Cohens Kappa: "
        + (
            f"{kappa:.2f}"
            if kappa is not None
            else "nicht berechenbar (ein Urteil ist immer gleich)"
        )
    )
    for object_id in result["disputed"]:
        st.button(
            f"Strittig, öffnen: {object_id}",
            key=f"agreement-open-{object_id}",
            on_click=actions.open_object,
            args=(object_id,),
        )


def search_panel(collection: list[ui.Current]) -> None:
    ui.section("Suche in der Sammlung")
    query = st.text_input("Suchbegriff", key="search-query")
    wanted = st.multiselect(
        "Status", search.STATUSES, default=search.STATUSES, key="search-status"
    )
    st.caption(
        "Sucht in Titel, Autor, Beschreibung, Suchbegriffen und Transkriptionen; Groß-/Kleinschreibung "
        "ist egal, typografische Varianten (etwa „Thür“ und „Tür“) bleiben verschieden."
    )
    hits = search.search(
        {cur.id: cur.record for cur in collection}, query, tuple(wanted)
    )
    for index, (object_id, name, text) in enumerate(hits):
        st.button(
            f"Öffnen: {object_id}" + (f" – {name}: {text}" if name else ""),
            key=f"search-open-{index}",
            on_click=actions.open_object,
            args=(object_id,),
        )
    if not hits:
        st.info("Keine Treffer.")


def colibri_path() -> Path:
    default = store.DATA_DIR / "colibri" / "ColibriImagesMetadataAnnotations.csv"
    return Path(os.environ.get("BILDLABOR_COLIBRI_CSV", default))


@st.cache_data(max_entries=2, show_spinner="Colibri-Datei wird gezählt ...")
def _aggregate(path: str, size: int, mtime_ns: int) -> colibri.Aggregate:
    return colibri.aggregate(Path(path))


def class_matrix(collection: list[ui.Current]) -> None:
    ui.section("Klassenabweichung: manuelle gegen automatische Klasse")
    st.caption(
        "Geprüft: lokale Stichprobe. Zählt alle Objekte der Stichprobe mit beiden Klassen, "
        f"auch solche, bei denen manuelle und automatische Klasse übereinstimmen "
        f"({len(collection)} Objekte)."
    )
    table, missing = matrix.cells(collection)
    titles = {cur.id: cur.record["source"]["scan_number"] for cur in collection}
    for (manual, automatic), ids in sorted(table.items()):
        with st.container(border=True, key=f"matrix-{manual}-{automatic}"):
            st.markdown(
                f"**manuell „{manual}“ x automatisch „{automatic}“:** {len(ids)}"
            )
            for object_id in ids:
                st.button(
                    f"Öffnen: Scan {titles[object_id]} ({object_id})",
                    key=f"matrix-open-{object_id}",
                    on_click=actions.open_object,
                    args=(object_id,),
                )
    if missing:
        st.caption(f"ohne Klasse: {len(missing)}")
    full_matrix(table)


def full_matrix(sample: dict[tuple[str, str], list[str]]) -> None:
    ui.section("Ganze Colibri-Datei: ungeprüft, nur gezählt")
    path = colibri_path()
    if not path.is_file():
        st.info(
            f"Die Colibri-CSV liegt nicht vor. Erwartet: {path} "
            "(Pfad änderbar über BILDLABOR_COLIBRI_CSV). Die App lädt sie nicht selbst herunter."
        )
        return
    if st.button("Gesamte Colibri-Datei auswerten", key="colibri-run"):
        st.session_state["colibri-shown"] = True
    if not st.session_state.get("colibri-shown"):
        return
    stat = path.stat()
    try:
        result = _aggregate(str(path), stat.st_size, stat.st_mtime_ns)
    except ValueError as error:
        st.error(str(error))
        return
    st.caption(
        "Colibris eigene Klassen, wie veröffentlicht: hier nicht geprüft und keine Ground Truth. "
        "Bei manchen Klassen überschreibt die manuelle Klasse die automatische; Übereinstimmungen "
        "messen daher nicht die Genauigkeit des Klassifikators. Die Zahlen sagen nicht, welche "
        "Klasse zutrifft. Mehrfachklassen stehen als eigene Zeile, etwa „Abbildung,Initiale“."
    )
    manuals = sorted({m for m, _ in result.cells})
    automatics = sorted({a for _, a in result.cells})
    st.dataframe(
        [
            {"manuell": m, **{a: result.cells.get((m, a), 0) for a in automatics}}
            | {"Summe": sum(result.cells.get((m, a), 0) for a in automatics)}
            for m in manuals
        ],
        hide_index=True,
        key="colibri-table",
    )
    st.caption(
        f"{result.rows} Zeilen; ohne manuelle Klasse: {result.without_manual}. "
        f"Davon lokal in der Stichprobe: {sum(len(ids) for ids in sample.values())} Objekte "
        "mit beiden Klassen."
    )
    if result.sha256 == colibri.MANIFEST_SHA256:
        st.caption("Prüfsumme entspricht dem Stand vom 06.11.2026.")
    else:
        st.caption("Abweichende Prüfsumme, Zahlen gelten für diese Datei.")
    disagreement_sample(path)


@st.cache_data(max_entries=2, show_spinner="Stichprobe wird gezogen ...")
def _sample(path: str, size: int, mtime_ns: int) -> list[dict[str, str]]:
    return colibri_sample.sample_disagreements(Path(path))


def disagreement_sample(path: Path) -> None:
    ui.section("Stichprobe abweichender Klassen")
    stat = path.stat()
    rows = _sample(str(path), stat.st_size, stat.st_mtime_ns)
    st.caption(
        "Bis zu drei Zeilen je Klassenpaar, bei denen manuelle und automatische Klasse "
        "abweichen; feste Zufallsauswahl, gleiche Datei gleiche Stichprobe. Nur Anzeige: "
        "nichts wird gespeichert, keine Ground Truth."
    )
    st.dataframe(
        [
            {
                "manuell": r["groundtruth"],
                "automatisch": r["classification"],
                "Scan": colibri_sample.scan_url(r),
            }
            for r in rows
        ],
        hide_index=True,
        key="colibri-sample",
        column_config={
            "Scan": st.column_config.LinkColumn("Scan", display_text="Scan öffnen")
        },
    )


def hero(cur: ui.Current) -> None:
    illustration = cur.record["region_annotations"][0]
    with st.container(key="collection-hero", border=True):
        text, picture = st.columns([7, 5], gap="large", vertical_alignment="center")
        with text:
            with st.container(key="hero-eyebrow"):
                st.caption("BILDARCHIV · FALLSTUDIE")
            st.title("Kinderbuch-Bildlabor")
            st.markdown(f"**{QUESTION}**")
            manual, automatic = review.classification_labels(cur.record) or ("", "")
            st.write(
                f"Colibri führt für diese Illustration die manuelle Klasse „{manual}“ "
                f"und die automatische Klasse „{automatic}“. Sie prüfen am Bild, welche zutrifft, begründen Ihre "
                "Entscheidung und exportieren sie mit Herkunft."
            )
            with st.container(horizontal=True):
                st.button(
                    "Leitbeispiel öffnen: Genovefa, Scan 22",
                    key="lead-open",
                    help="Hier beginnen. Der Prüfpfad führt vom Bildausschnitt bis zum Export.",
                    on_click=actions.open_object,
                    args=(cur.id,),
                    type="primary",
                    icon=":material/arrow_forward:",
                )
                st.button(
                    "Eigenes Buch importieren",
                    key="import-start",
                    on_click=lambda: st.session_state.update(view="import"),
                )
            st.caption(
                "Fünf Schritte: Rahmen prüfen → Klassen vergleichen → "
                "Beschreibung prüfen → Prüfung abschließen → exportieren"
            )
        with picture:
            st.image(
                regions.crop(ui.page_image(cur.src.page_image), illustration["xywh"]),
                width="stretch",
                alt="Historische Illustration mit zwei Figuren in einem Gewölbe",
                caption="Genovefa · Augsburg 1810 · Scan 22",
            )


def case_study(collection: list[ui.Current]) -> None:
    ui.section("Fallstudie: fünf abweichende Klassifikationen in „Genovefa“")
    st.caption(
        "Auswahl: alle fünf Abbildungen aus „Genovefa“ (Augsburg 1810, PPN1772789429), zu denen "
        "Colibri eine manuelle Klasse enthält. Sie lautet jeweils „Abbildung“; die automatische "
        "Klasse weicht in allen fünf ab. Zahlen gelten nur für diese fünf ausgewählten Beispiele, "
        "nicht für Colibri insgesamt. Die Spalte „Entscheidung am Bild“ zeigt den Stand Ihres "
        "Datenordners; nach einem frischen Start ist sie überall offen."
    )
    rows = []
    for cur in collection:
        labels = review.classification_labels(cur.record)
        if not labels:
            continue
        source = cur.record["source"]
        message = review.classification_message(cur.record)
        assert message
        entry = review.decision(cur.record, review.CLASSIFICATION, message)
        rows.append(
            {
                "Scan": source["scan_number"],
                "Seite laut METS": source.get("page_label_mets"),
                "Colibri manuell": labels[0],
                "Colibri automatisch": labels[1],
                "Entscheidung am Bild": entry["outcome_de"] if entry else "offen",
                "Leitbeispiel": "ja" if cur.id == LEAD else "",
            }
        )
    st.dataframe(rows, hide_index=True)


def second_example(record: dict) -> None:
    biblio = record["bibliographic_metadata_from_colibri"]
    transcription = record["transcription"]
    ui.section("Zweites Beispiel: „Die Heimath in Amerika“")
    st.markdown(
        f"- **Buch laut Katalog** (Colibri, MODS): {biblio['publication_place']}, "
        f"{biblio['publisher']}\n"
        "- **Aufdruck auf dem Bildblatt** (vorläufige Lesung): "
        f"„{transcription['working_publisher_statement']}“\n"
        "- Zwei Kontexte, zwei Felder: Keine Angabe überschreibt die andere. Dazu wird die "
        "gespeicherte OCR-Ausgabe des Bildtitels neben der Lesung am Bildausschnitt geprüft."
    )
    st.button(
        "Zweites Beispiel öffnen",
        key="second-open",
        on_click=actions.open_object,
        args=(SECOND,),
    )


def glossary() -> None:
    with st.expander("Begriffe kurz erklärt"):
        st.markdown("\n".join(f"- **{term}:** {text}" for term, text in TERMS))


def card(cur: ui.Current, records: list[dict]) -> None:
    record, source = cur.record, cur.record["source"]
    biblio = record["bibliographic_metadata_from_colibri"]
    illustration = record["region_annotations"][0]
    icon, _, word, color = workflow.object_state(record)
    st.badge(word, icon=icon, color=color)
    st.image(
        thumbnail(cur.src.page_image, tuple(illustration["xywh"])),
        width="stretch",
        alt=f"Illustration aus {biblio['title']}, Scan {source['scan_number']}",
    )
    st.markdown(
        f"**{biblio['title']}** ({biblio['publication_place'] or 'Ort unbekannt'}, {biblio['publication_date'] or 'Jahr unbekannt'})  \n"
        f"Scan {source['scan_number']}"
        + (
            f", Seite {source['page_label_mets']} laut METS"
            if source.get("page_label_mets")
            else ""
        )
    )
    labels = review.classification_labels(record)
    if labels:
        with st.container(horizontal=True, gap="xsmall"):
            st.badge(f"manuell: {labels[0]}", color="gray")
            st.badge(
                f"maschinell: {labels[1]}", icon=":material/smart_toy:", color="violet"
            )
        st.caption(f"Colibri: manuell „{labels[0]}“, automatisch „{labels[1]}“")
    areas = review.review_areas(record)
    done = sum(a["done"] for a in areas)
    st.progress(
        done / len(areas), text=f"{done} von {len(areas)} Prüfbereichen bestätigt"
    )
    st.caption(
        review.readiness(record, validate.run_all(cur.working, cur.src, records))
    )
    st.button(
        "Objekt öffnen",
        key=f"open-{cur.id}",
        on_click=actions.open_object,
        args=(cur.id,),
        width="stretch",
    )


def collection_export(collection: list[ui.Current]) -> None:
    ui.section("Sammlungsübersicht exportieren")
    st.caption(
        "Eine CSV-Datei mit einer Zeile je Region aller Objekte, mit Prüfständen, Herkunft und Rechten. "
        "Vollständige JSON-Exporte entstehen je Objekt im Reiter „Export“."
    )
    st.button(
        "Sammlungsübersicht als CSV exportieren",
        key="collection-export",
        on_click=actions.run_collection_export,
    )
    path = store.EXPORT_DIR / actions.COLLECTION_CSV
    if path.exists():
        st.caption(f"Vorhanden: {path.relative_to(store.DATA_DIR)}")
