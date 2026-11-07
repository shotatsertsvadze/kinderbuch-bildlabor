"""Reiter „Klassifikation“ und Formular für begründete Entscheidungen zu fachlichen Hinweisen."""

import xml.etree.ElementTree as ET

import streamlit as st

from kinderbuch_bildlabor import actions, export, oai, regions, review, ui
from kinderbuch_bildlabor.library_view import parsed_source
from kinderbuch_bildlabor.ui import Current

EXPORT_FIELDS = [
    "colibri_klasse_manuell",
    "colibri_klasse_automatisch",
    "klassifikation_stand",
    "klassifikation_entscheidung",
    "klassifikation_begruendung",
    "klassifikation_person",
    "klassifikation_am",
    "x",
    "y",
    "breite",
    "hoehe",
    "regionen_pruefstatus",
]


def classification_tab(cur: Current) -> None:
    record, source = cur.record, cur.record["source"]
    message = review.classification_message(record)
    assert message
    manual, automatic = review.classification_labels(record) or ("", "")
    illustration = next(
        r for r in record["region_annotations"] if r["region_type"] == "illustration"
    )
    st.markdown(
        "**Frage:** Welche Klasse beschreibt diese Abbildung zutreffend? Zwei Angaben aus "
        "demselben Datensatz widersprechen sich. Entschieden wird am Originalbild, mit Begründung "
        "und Namen; beide Ausgangswerte bleiben unverändert erhalten."
    )
    left, right = ui.image_and_controls()
    with left:
        st.image(
            regions.crop(ui.page_image(cur.src.page_image), illustration["xywh"]),
            width="stretch",
            caption=f"Markierte Region {illustration['xywh']} (Pixel im Scan {source['scan_number']})",
            alt="Ausschnitt der markierten Illustration aus der gescannten Seite.",
        )
        st.image(
            regions.draw_regions(
                ui.page_image(cur.src.page_image), record["region_annotations"]
            ),
            width="stretch",
            caption="Gesamtseite mit der markierten Region",
            alt="Gescannte Buchseite; die Region der Illustration ist als Rahmen markiert.",
        )
    with right:
        ui.section("Zwei Angaben in Colibri")
        st.dataframe(
            [
                {
                    "Herkunft": "Manuelle Annotation (Colibri-Spalte „groundtruth“)",
                    "Klasse": manual,
                },
                {
                    "Herkunft": "Automatische Klassifikation (Spalte „classification“)",
                    "Klasse": automatic,
                },
            ],
            hide_index=True,
        )
        st.caption(
            "Die Spalte heißt in Colibri „groundtruth“. Hier wird sie trotzdem am Bild geprüft: "
            "Ground Truth bedeutet eine geprüfte Referenz, und ob sie zutrifft, ist genau die Frage. "
            f"Quelle: {source['colibri_file_reference']}."
        )
        ui.section("Belege am Original")
        evidence(cur, illustration)
        ui.section("Entscheidung")
        decision_form(cur, review.CLASSIFICATION, message)
        ui.section("Was im Export erhalten bleibt")
        row = next(
            r
            for r in export.csv_rows(record, "")
            if r["region_id"] == illustration["id"]
        )
        st.dataframe(
            [
                {"CSV-Spalte": k, "Wert": "leer" if row[k] is None else str(row[k])}
                for k in EXPORT_FIELDS
            ],
            hide_index=True,
        )
        st.caption(
            "Der JSON-Export enthält zusätzlich die vollständige Entscheidung mit Grundlage und das "
            "Prüfprotokoll. Ändert sich die Region später, wird die Entscheidung aufgehoben und muss "
            "neu getroffen werden; die alte Begründung bleibt im Protokoll."
        )


def evidence(cur: Current, illustration: dict) -> None:
    record, source = cur.record, cur.record["source"]
    description = record["image_description"]
    lines = [
        f"Regionsgrenzen: {review.status_label(illustration['review_status'])}",
        f"Bildbeschreibung ({review.status_label(description['review_status'])}): "
        f"{description['working_description_de']}",
    ]
    try:
        root = parsed_source(cur.src.oai_record)
        structure = oai.structure_for_page(root, source["physical_page_id"])
        label = oai.page_label(root, source["physical_page_id"])
    except (ET.ParseError, oai.MissingMetadata):
        structure, label = None, None
    if structure:
        lines.append(
            f"METS: {source['physical_page_id']} gehört zu {structure['type_de']} "
            f"„{structure['title'] or structure['label']}“, Seitenbezeichnung „{label}“; "
            "die Abbildung selbst ist im METS nicht eigens ausgezeichnet"
        )
    st.markdown("\n".join(f"- {line}" for line in lines))
    st.link_button(
        "Scan in der Originalansicht öffnen",
        source["viewer_url"],
        icon=":material/open_in_new:",
    )


def decision_form(cur: Current, code: str, message: str) -> None:
    record = cur.record
    entry = review.decision(record, code, message)
    if entry is None:
        st.warning("Offen: noch keine Entscheidung festgehalten.", icon=ui.PENDING)
    else:
        show = st.success if review.resolves(entry) else st.info
        show(
            f"**{entry['outcome_de']}**  \nBegründung: {entry['rationale_de']}  \n"
            f"Festgehalten von {entry['by']} am {ui.local_time(entry['at'])}",
            icon=ui.CONFIRMED if review.resolves(entry) else ui.PENDING,
        )
    key = actions.decision_key(cur.id, code, message)
    holder = st.container() if entry is None else st.expander("Entscheidung ändern")
    with holder, st.form(key, enter_to_submit=False):
        st.radio(
            "Entscheidung",
            review.decision_options(code, record),
            index=None,
            key=f"{key}-outcome",
        )
        st.text_area(
            "Begründung: Welche Belege am Bild haben Sie herangezogen?",
            key=f"{key}-rationale",
            height=ui.TEXT_AREA_HEIGHT,
        )
        st.form_submit_button(
            "Entscheidung mit Namen speichern",
            key=f"{key}-submit",
            on_click=actions.record_decision,
            args=(cur.id, code, message, review.decision_basis(record, code)),
        )
    if error := st.session_state.pop(f"{key}-error", None):
        st.error(error, icon=ui.ERROR)
    st.caption(
        "„Nicht entscheidbar“ hält die Begründung fest, lässt den Hinweis aber offen und "
        "blockierend. Eine Entscheidung ist keine Ground-Truth-Freigabe."
    )
