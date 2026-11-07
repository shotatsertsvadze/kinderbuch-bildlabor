"""Reiter „Klassifikation“ und Formular für begründete Entscheidungen zu fachlichen Hinweisen."""

import xml.etree.ElementTree as ET

import streamlit as st

from kinderbuch_bildlabor import actions, export, oai, regions, review, ui, workflow
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
    left, right = ui.image_and_controls()
    with left:
        st.image(
            regions.crop(ui.page_image(cur.src.page_image), illustration["xywh"]),
            width="stretch",
            caption=f"Markierte Region {illustration['xywh']} (Pixel im Scan {source['scan_number']})",
            alt="Ausschnitt der markierten Illustration aus der gescannten Seite.",
        )
        ui.subsection("Belege am Original")
        evidence(cur, illustration)
        st.image(
            regions.draw_regions(
                ui.page_image(cur.src.page_image), record["region_annotations"]
            ),
            width="stretch",
            caption="Gesamtseite mit der markierten Region",
            alt="Gescannte Buchseite; die Region der Illustration ist als Rahmen markiert.",
        )
    with right:
        ui.section("Welche Klasse trifft zu?")
        st.markdown(
            "Colibri nennt zwei Klassen. Wählen Sie am Bild die zutreffende und nennen Sie Ihre "
            "Belege. Beide Ausgangswerte bleiben erhalten."
        )
        groundtruth = (
            "Steht in Colibri in der Spalte „groundtruth“; wird hier trotzdem am Bild geprüft. "
            f"Quelle: {source['colibri_file_reference']}."
        )
        manual_box, automatic_box = st.columns(2)
        manual_box.metric("Colibri manuell", manual, help=groundtruth, border=True)
        automatic_box.metric(
            "Colibri automatisch",
            automatic,
            help="Automatische Klassifikation (Colibri-Spalte „classification“).",
            border=True,
        )
        entry = decision_form(cur, review.CLASSIFICATION, message)
        if review.resolves(entry):
            workflow.continue_button(
                cur.id, record, f"{cur.id}-classification-continue"
            )
        with st.expander("Was im Export erhalten bleibt"):
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
                "Der JSON-Export enthält zusätzlich die vollständige Entscheidung mit Grundlage und "
                "das Prüfprotokoll. Ändert sich die Region später, wird die Entscheidung aufgehoben "
                "und muss neu getroffen werden; die alte Begründung bleibt im Protokoll."
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


def decision_form(cur: Current, code: str, message: str) -> dict | None:
    record = cur.record
    entry = review.decision(record, code, message)
    if entry is None:
        st.warning(
            "Offen: Antwort wählen, begründen, mit Namen speichern.", icon=ui.PENDING
        )
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
        if not actions.reviewer():
            st.caption(
                f"{ui.LOCK} Zum Speichern wird Ihr Name benötigt: oben im Prüfpfad unter "
                "„Prüfende Person“."
            )
        st.form_submit_button(
            "Entscheidung mit Namen speichern",
            key=f"{key}-submit",
            type="primary",
            on_click=actions.record_decision,
            args=(cur.id, code, message, review.decision_basis(record, code)),
        )
    if error := st.session_state.pop(f"{key}-error", None):
        st.error(error, icon=ui.ERROR)
    st.caption(
        "„Nicht entscheidbar“ hält die Begründung fest, lässt den Hinweis aber offen und "
        "blockierend. Eine Entscheidung ist keine Ground-Truth-Freigabe."
    )
    return entry
