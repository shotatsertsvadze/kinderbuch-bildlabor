"""Reiter eines Objekts: Übersicht, Regionen, Beschreibung und Transkription."""

import streamlit as st

from kinderbuch_bildlabor import actions, regions, review, store, ui
from kinderbuch_bildlabor.ui import Current


def overview_tab(cur: Current) -> None:
    record, source = cur.record, cur.record["source"]
    biblio = record["bibliographic_metadata_from_colibri"]
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.image(regions.draw_regions(ui.page_image(cur.src.page_image), record["region_annotations"]),
                 width="stretch", caption="Gesamtseite mit den gespeicherten Regionen (Vergrößern: Symbol oben rechts)")
    with right:
        st.markdown("#### Buch")
        st.markdown(
            f"**{biblio['title']}**  \n"
            f"Verfasser: {biblio['author_display']}  \n"
            f"Erschienen: {biblio['publication_place']}, {biblio['publication_date']}  \n"
            f"Verlag: {biblio['publisher'] or 'nicht angegeben (weder in Colibri noch im MODS)'}")
        st.caption("Bibliografische Angaben aus Colibri; Abgleich mit METS/MODS im Reiter „Bibliotheksdaten“.")
        st.markdown("#### Seite")
        label = source.get("page_label_mets")
        st.markdown(
            f"Scan {source['scan_number']} im Digitalisat ({source['physical_page_id']})  \n"
            + (f"Seitenbezeichnung im METS: „{label}“; gedruckte Seitenzahl am Scan noch nicht bestätigt"
               if label else "Gedruckte Seitenzahl unbekannt; Scan-Nummer ist keine Seitenzahl"))
        st.link_button("Originalansicht der Staatsbibliothek öffnen", source["viewer_url"],
                       icon=":material/open_in_new:")
        st.markdown("#### Bildbeschreibung")
        ui.source_text(record["image_description"]["working_description_de"])
        ui.status_badge(record["image_description"]["review_status"])
        st.markdown("#### Rechte und Herkunft")
        st.markdown(f"Quellwerk: {biblio['rights_statement']}  \n"
                    f"Colibri-Datensatz: [CC BY 4.0]({source['colibri_dataset_license']}) – "
                    f"{source['colibri_dataset_credit']}")
        if source.get("colibri_groundtruth"):
            st.caption(f"Colibri-Annotation dieser Abbildung: manuell „{source['colibri_groundtruth']}“, "
                       f"automatisch „{source['colibri_classification']}“.")

    progress_table(record)
    if "working_publisher_statement" in (record.get("transcription") or {}):
        imprint_comparison(record)
    st.markdown("#### Fachliche Hinweise")
    with st.container(border=True):
        for item in record["review_items"]:
            st.markdown(f"- {item['note_de']}")
    with st.expander("Technische Angaben"):
        st.text(f"Objekt-ID: {record['id']}\nPPN: {source['ppn']}\n"
                f"Colibri-Datei: {source['colibri_file_reference']}\nBildinfo (IIIF): {source['image_info_url']}\n"
                f"Quelldatei (nur gelesen): {cur.working['based_on']['file']}\n"
                f"Arbeitskopie: {store.work_path(record['id']).relative_to(store.DATA_DIR)}")


def progress_table(record: dict) -> None:
    areas = review.review_areas(record)
    st.markdown(f"#### Prüfbereiche: {sum(a['done'] for a in areas)} von {len(areas)} bestätigt")
    st.dataframe([{"Stand": "Bestätigt" if a["done"] else "Offen", "Bereich": a["label_de"],
                   "Prüfstand": review.status_label(a["status"]), "Reiter": a["tab_de"]} for a in areas],
                 hide_index=True)


def imprint_comparison(record: dict) -> None:
    biblio = record["bibliographic_metadata_from_colibri"]
    st.markdown("#### Verlagsangaben im Vergleich")
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("**Bibliografische Angabe (Colibri, MODS)**")
        st.text(f"Ort: {biblio['publication_place']}\nVerlag: {biblio['publisher']}")
    with right, st.container(border=True):
        st.markdown("**Aufdruck auf dem Bildblatt (vorläufige Lesung)**")
        ui.source_text(record["transcription"]["working_publisher_statement"])
        ui.status_badge(record["transcription"]["review_status_by_field"]["working_publisher_statement"])
    st.caption("Beide Angaben bleiben mit ihrem Bezug erhalten. Die Abweichung wird zur Prüfung angezeigt, "
               "nicht als Katalogfehler gewertet und nicht angeglichen.")


def region_option(record: dict, region: dict) -> str:
    # Feste Beschriftung: ändert sich der Text (z. B. Status), verliert das Frontend die Auswahl
    return f"{record['region_annotations'].index(region) + 1} · {region['label_de']}"


def region_tab(cur: Current) -> None:
    record = cur.record
    by_id = {r["id"]: r for r in record["region_annotations"]}
    choice = next(iter(by_id))
    if len(by_id) > 1:
        choice = st.radio("Region auswählen", list(by_id), format_func=lambda i: region_option(record, by_id[i]),
                          horizontal=True, key=f"{cur.id}-region-choice")
    left, right = st.columns([2, 3], gap="large")
    with right:
        preview_xywh = region_editor(cur, by_id[choice])
    with left:
        preview = [{**r, "xywh": preview_xywh} if r["id"] == choice else r for r in record["region_annotations"]]
        st.image(regions.draw_regions(ui.page_image(cur.src.page_image), preview), width="stretch",
                 caption="Gesamtseite; die gewählte Region mit den aktuell eingegebenen Werten")
    width, height = cur.size
    st.caption(f"Koordinaten sind Pixel [x, y, Breite, Höhe] im Ausgangsbild {width} × {height}, gezählt ab der "
               "linken oberen Ecke. Die verkleinerte Anzeige ändert sie nicht.")


def crop_width(xywh: list[int], max_width: int = 560, max_height: int = 420) -> int:
    """Anzeigebreite so, dass auch hohe Regionen nicht übermäßig viel Platz einnehmen."""
    w, h = xywh[2], xywh[3]
    return max(1, min(w, max_width, round(max_height * w / h)))


def region_editor(cur: Current, region: dict) -> list[int]:
    """Bearbeitung einer Region; liefert die für die Vorschau gültigen Koordinaten."""
    region_id = region["id"]
    width, height = cur.size
    st.markdown(f"#### Region {region_option(cur.record, region)}")
    ui.status_badge(region["review_status"])
    ui.origin_note(region.get("region_origin_de"))
    keys = actions.xywh_keys(region_id)
    sync = ui.sync_fields(keys, region["xywh"])
    cols = st.columns(4)
    for col, key, label, limit in zip(cols, keys, ["x (links)", "y (oben)", "Breite", "Höhe"],
                                      [width, height, width, height]):
        col.number_input(label, min_value=0, max_value=limit, step=1, key=key)
    xywh = actions.input_xywh(region_id)
    problems = regions.bounds_problems(xywh, width, height)
    for problem in problems:
        st.error(problem, icon=":material/error:")
    if sync == ui.CONFLICT:
        ui.conflict_note(keys, region["xywh"], str(region["xywh"]))
    ui.edit_state(sync, f"Gespeichert ist {region['xywh']}. Speichern setzt den Prüfstand dieser Region zurück.")
    shown = region["xywh"] if problems else xywh
    st.image(regions.crop(ui.page_image(cur.src.page_image), shown), width=crop_width(shown),
             caption="Ausschnitt mit den eingegebenen Werten" if sync != ui.CLEAN else "Ausschnitt (gespeicherter Stand)")
    buttons = st.columns(2)
    buttons[0].button("Koordinaten speichern", key=f"{region_id}-save", on_click=actions.save_coordinates,
                      args=(cur.id, region_id), disabled=sync != ui.EDITED or bool(problems))
    buttons[1].button("Eingaben verwerfen", key=f"{region_id}-discard", on_click=ui.load_fields,
                      args=(keys, region["xywh"]), disabled=sync != ui.EDITED)

    st.divider()
    if region["review_status"] == review.REGION_REVIEWED:
        ui.confirmed_note(cur.record, region_id)
    else:
        ui.confirm_controls(
            f"{region_id}-review",
            "Die gespeicherten Grenzen umfassen den Bereich vollständig und knapp. "
            "Keine Aussage über Bildinhalt oder Transkription.",
            "Ich habe die gespeicherten Grenzen dieser Region am Bild geprüft.",
            actions.confirm_region, (cur.id, region_id, region["xywh"]),
            blocked_de="Erst die Eingaben speichern oder verwerfen." if sync != ui.CLEAN else None)
    return shown


def description_tab(cur: Current) -> None:
    illustration = next((r for r in cur.record["region_annotations"] if r["region_type"] == "illustration"), None)
    left, right = st.columns([2, 3], gap="large")
    with left:
        if illustration:
            st.image(regions.crop(ui.page_image(cur.src.page_image), illustration["xywh"]), width="stretch",
                     caption="Ausschnitt der Illustration (gespeicherte Grenzen)")
    with right:
        description_editor(cur)
        for region in cur.record["region_annotations"]:
            if "keywords_de" in region:
                st.divider()
                keyword_editor(cur, region)


def description_editor(cur: Current) -> None:
    description = cur.record["image_description"]
    st.markdown("#### Bildbeschreibung")
    ui.status_badge(description["review_status"])
    ui.origin_note(description.get("description_origin_de"))
    st.caption(f"Objektart: {description['object_type']} · Illustrator: unbekannt (bewusst leer; Buchautor und "
               "Illustrator sind verschiedene Rollen)")
    key, stored = actions.description_key(cur.id), description["working_description_de"]
    sync = ui.sync_fields([key], [stored], lambda values: [values[0].strip()])
    st.text_area("Bildbeschreibung (sichtbarer Inhalt, ohne Deutung)", key=key, height=140)
    if sync == ui.CONFLICT:
        ui.conflict_note([key], [stored], f"„{stored}“")
    ui.edit_state(sync, "Speichern setzt die Bestätigung der Beschreibung zurück.")
    st.button("Beschreibung speichern", key=f"{key}-save", on_click=actions.save_description, args=(cur.id,),
              disabled=sync != ui.EDITED)
    if description["observation_de"] != stored:
        with st.expander("Erste Beobachtung (unverändert)"):
            ui.source_text(description["observation_de"])
    if description["review_status"] == review.DESCRIPTION_REVIEWED:
        ui.confirmed_note(cur.record, "image_description")
    else:
        ui.confirm_controls(
            f"{key}-review", "Die gespeicherte Beschreibung gibt den sichtbaren Bildinhalt zutreffend wieder.",
            "Ich habe die Beschreibung am Bild geprüft.", actions.confirm_description, (cur.id, stored),
            blocked_de="Erst die Eingabe speichern oder verwerfen." if sync != ui.CLEAN else None)


def keyword_editor(cur: Current, region: dict) -> None:
    region_id = region["id"]
    st.markdown(f"#### Suchbegriffe: {region['label_de']}")
    ui.status_badge(region["keyword_review_status"])
    ui.origin_note(region.get("keyword_origin_de"))
    st.caption("Projektlokale Begriffe, keine geprüften GND-Verknüpfungen.")
    key, stored = actions.keyword_key(region_id), ["\n".join(region["keywords_de"])]
    sync = ui.sync_fields([key], stored, lambda values: [actions.keyword_list(values[0])])
    st.text_area("Ein Begriff pro Zeile", key=key, height=130)
    if sync == ui.CONFLICT:
        ui.conflict_note([key], stored, "; ".join(region["keywords_de"]))
    ui.edit_state(sync, "Speichern setzt die Bestätigung der Suchbegriffe zurück.")
    st.button("Suchbegriffe speichern", key=f"{key}-save", on_click=actions.save_keywords,
              args=(cur.id, region_id), disabled=sync != ui.EDITED)
    if region["keyword_review_status"] == review.KEYWORDS_ACCEPTED:
        ui.confirmed_note(cur.record, f"{region_id}/keywords_de")
    else:
        ui.confirm_controls(
            f"{key}-review", "Die gespeicherten Begriffe beschreiben den Bildinhalt zutreffend.",
            "Ich habe die Suchbegriffe am Bild geprüft.", actions.confirm_keywords,
            (cur.id, region_id, region["keywords_de"]),
            blocked_de="Erst die Eingabe speichern oder verwerfen." if sync != ui.CLEAN else None)


def transcription_tab(cur: Current) -> None:
    transcription = cur.record["transcription"]
    st.badge("Keine Ground Truth", icon=":material/block:", color="gray")
    st.caption(f"{transcription['review_note_de']} Bildtitel und Verlagsangabe werden einzeln geprüft.")
    ocr = cur.record.get("ocr_result")
    for region in cur.record["region_annotations"]:
        if region.get("transcription_field"):
            with st.container(border=True):
                transcription_editor(cur, region, ocr if ocr and ocr["region_id"] == region["id"] else None)
    with st.expander("Erste Lesung (unverändert, mit Zeilenumbruch)"):
        st.code(transcription["initial_user_transcription"], language=None)


def transcription_editor(cur: Current, region: dict, ocr: dict | None) -> None:
    transcription = cur.record["transcription"]
    field = region["transcription_field"]
    status = transcription["review_status_by_field"][field]
    st.markdown(f"#### {region['label_de']}")
    ui.status_badge(status)
    st.image(regions.crop(ui.page_image(cur.src.page_image), region["xywh"]), width=min(region["xywh"][2], 730),
             caption="Vorlage: Ausschnitt aus dem Scan")
    key = actions.transcription_key(cur.id, field)
    sync = ui.sync_fields([key], [transcription[field]])
    columns = st.columns(2 if ocr else 1, gap="large")
    with columns[0]:
        st.text_input("Arbeitstranskription (zeichengetreu, historische Schreibweise beibehalten)", key=key)
        if sync == ui.CONFLICT:
            ui.conflict_note([key], [transcription[field]], f"„{transcription[field]}“")
        ui.edit_state(sync, "Speichern setzt nur den Prüfstand dieses Textes auf „vorläufig“.")
        st.button("Transkription speichern", key=f"{key}-save", on_click=actions.save_transcription,
                  args=(cur.id, field), disabled=sync != ui.EDITED)
    if ocr:
        with columns[1]:
            ocr_block(cur, ocr)
    if status == review.TRANSCRIPTION_REVIEWED:
        ui.confirmed_note(cur.record, f"transcription/{field}")
    else:
        ui.confirm_controls(
            f"{key}-review",
            f"Die gespeicherte Lesung „{region['label_de']}“ stimmt mit der Vorlage überein. "
            "Das ist keine Freigabe als Ground Truth.",
            "Ich habe diesen Text an der Vorlage geprüft.",
            actions.confirm_transcription, (cur.id, field, transcription[field]),
            blocked_de="Erst die Eingabe speichern oder verwerfen." if sync != ui.CLEAN else None)


def ocr_block(cur: Current, ocr: dict) -> None:
    meta = store.read_json(cur.src.record.parent / ocr["result_file"])
    st.markdown("**Gespeicherte OCR-Ausgabe** (unverändert, ungeprüft)")
    st.code(ocr["raw_text"], language=None)
    st.caption(f"{meta['engine_version']}, Modell {meta['language_model']}, ohne Vorverarbeitung. "
               "Ein einzelner Versuch, keine Bewertung der OCR-Qualität.")
    with st.expander("Technische Angaben zum OCR-Lauf"):
        st.text(f"Genaue Zeichenfolge: {ocr['raw_text']!r} ({len(ocr['raw_text'])} Zeichen)\n"
                f"Modellrevision {meta['model_revision']}\n"
                f"OEM {meta['engine_mode']}, PSM {meta['page_segmentation_mode']}, "
                f"Vorverarbeitung: {meta['preprocessing']}\n"
                f"Eingabebild: {meta['input_file']} (SHA-256 {meta['input_sha256'][:16]}…)")
