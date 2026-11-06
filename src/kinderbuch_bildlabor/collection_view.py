"""Startseite: Zweck, Ablauf und die Objekte der Sammlung mit ihrem Prüfstand."""

import streamlit as st
from PIL import Image

from kinderbuch_bildlabor import actions, regions, review, store, ui, validate

STEPS = [
    (
        "Quelle",
        "Digitalisat, IIIF-Bild und METS/MODS der Staatsbibliothek, Metadaten aus Colibri",
    ),
    ("Regionen", "Illustration und Textbereiche als Pixelrechtecke im Originalbild"),
    ("Beschreibung", "sichtbarer Bildinhalt und projektlokale Suchbegriffe"),
    (
        "Transkription",
        "Bildtitel und Aufdrucke zeichengetreu, neben der gespeicherten OCR-Ausgabe",
    ),
    (
        "Prüfung",
        "jeder Bereich wird einzeln am Bild bestätigt; Änderungen setzen nur ihn zurück",
    ),
    (
        "Export",
        "JSON und CSV mit Herkunft, Rechten und Prüfprotokoll, mit Rückladeprüfung",
    ),
]


@st.cache_resource
def thumbnail(path, xywh: tuple[int, ...]) -> Image.Image:
    image = regions.crop(ui.page_image(path), list(xywh))
    image.thumbnail((420, 300))
    return image


def render(collection: list[ui.Current]) -> None:
    st.title("Kinderbuch-Bildlabor")
    st.markdown(
        "Erschließung und Qualitätsprüfung von Illustrationen aus digitalisierten Kinder- und "
        "Jugendbüchern des 19. Jahrhunderts der Staatsbibliothek zu Berlin. Der Prototyp zeigt an einer "
        "kleinen Stichprobe, wie Bildregionen, Beschreibungen und Transkriptionen nachvollziehbar "
        "erfasst, einzeln geprüft und mit Herkunft und Rechten exportiert werden."
    )
    st.info(
        "Alle Angaben sind Arbeitsstände. Grenzen, Beschreibungen und Lesungen gelten erst nach "
        "ausdrücklicher Bestätigung durch eine prüfende Person als geprüft; nichts davon ist Ground Truth.",
        icon=":material/info:",
    )

    st.markdown("#### Ablauf je Objekt")
    st.markdown(
        "\n".join(
            f"{n}. **{name}:** {text}" for n, (name, text) in enumerate(STEPS, start=1)
        )
    )

    books = {cur.record["source"]["ppn"] for cur in collection}
    st.markdown(
        f"#### Stichprobe: {len(collection)} Illustrationen aus {len(books)} Büchern"
    )
    columns = st.columns(3)
    for index, cur in enumerate(collection):
        with columns[index % 3], st.container(border=True):
            card(cur)
    collection_export(collection)


def card(cur: ui.Current) -> None:
    record, source = cur.record, cur.record["source"]
    biblio = record["bibliographic_metadata_from_colibri"]
    illustration = record["region_annotations"][0]
    st.image(
        thumbnail(cur.src.page_image, tuple(illustration["xywh"])), width="stretch"
    )
    st.markdown(
        f"**{biblio['title']}** ({biblio['publication_place']} {biblio['publication_date']})  \n"
        f"Scan {source['scan_number']}"
        + (
            f", Seite {source['page_label_mets']} laut METS"
            if source.get("page_label_mets")
            else ""
        )
    )
    areas = review.review_areas(record)
    done = sum(a["done"] for a in areas)
    st.progress(
        done / len(areas), text=f"{done} von {len(areas)} Prüfbereichen bestätigt"
    )
    records = [store.load_working_copy(src)["record"] for src in store.catalog()]
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
    st.markdown("#### Sammlungsübersicht exportieren")
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
