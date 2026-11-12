"""Startseite: Leitfrage, Fallstudie, Einstieg, Begriffe und die Objekte der Sammlung."""

import streamlit as st
from PIL import Image

from kinderbuch_bildlabor import (
    actions,
    example_view,
    regions,
    review,
    store,
    ui,
    validate,
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
    st.button(
        "Eigenes Buch importieren",
        key="import-start",
        on_click=lambda: st.session_state.update(view="import"),
    )
    by_id = {cur.id: cur for cur in collection}
    hero(by_id[LEAD])
    example_view.render()
    case_study(collection)
    second_example(by_id[SECOND].record)
    glossary()

    books = {
        cur.record["source"]["ppn"] or cur.record["metadata_provenance"]["title"]
        for cur in collection
    }
    ui.section(f"Stichprobe: {len(collection)} Illustrationen aus {len(books)} Büchern")
    columns = st.columns(3)
    records = [cur.record for cur in collection]
    for index, cur in enumerate(collection):
        with columns[index % 3], st.container(border=True):
            card(cur, records)
    collection_export(collection)


def hero(cur: ui.Current) -> None:
    illustration = cur.record["region_annotations"][0]
    with st.container(key="collection-hero", border=True):
        text, picture = st.columns([6, 5], gap="large", vertical_alignment="center")
        with text:
            st.caption("BILDARCHIV · FALLSTUDIE")
            st.title("Kinderbuch-Bildlabor")
            st.markdown(f"**{QUESTION}**")
            manual, automatic = review.classification_labels(cur.record) or ("", "")
            st.write(
                f"Colibri führt für diese Illustration die manuelle Klasse „{manual}“ "
                f"und die automatische Klasse „{automatic}“. Sie prüfen am Bild, welche zutrifft, begründen Ihre "
                "Entscheidung und exportieren sie mit Herkunft."
            )
            st.button(
                "Leitbeispiel öffnen: Genovefa, Scan 22",
                key="lead-open",
                help="Hier beginnen. Der Prüfpfad führt vom Bildausschnitt bis zum Export.",
                on_click=actions.open_object,
                args=(cur.id,),
                type="primary",
                icon=":material/arrow_forward:",
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
