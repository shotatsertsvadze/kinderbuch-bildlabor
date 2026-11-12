"""Reiter eines Objekts: Übersicht, Regionen, Beschreibung und Transkription."""

import streamlit as st

from kinderbuch_bildlabor import (
    actions,
    ocr,
    region_canvas,
    regions,
    review,
    store,
    ui,
    workflow,
)
from kinderbuch_bildlabor.ui import Current


def overview_tab(cur: Current) -> None:
    record, source = cur.record, cur.record["source"]
    biblio = record["bibliographic_metadata_from_colibri"]
    left, right = ui.image_and_controls()
    with left:
        st.image(
            regions.draw_regions(
                ui.page_image(cur.src.page_image), record["region_annotations"]
            ),
            width="stretch",
            caption="Gesamtseite mit den gespeicherten Regionen (Vergrößern: Symbol oben rechts)",
            alt="Gescannte Buchseite; die gespeicherten Regionen sind als nummerierte Rahmen markiert.",
        )
    with right:
        ui.section("Buch")
        st.markdown(
            f"**{biblio['title']}**  \n"
            f"Verfasser: {biblio['author_display'] or 'unbekannt'}  \n"
            f"Erschienen: {biblio['publication_place'] or 'unbekannt'}, "
            f"{biblio['publication_date'] or 'unbekannt'}  \n"
            f"Verlag: {biblio['publisher'] or 'nicht angegeben'}"
        )
        st.caption(
            "Metadaten aus dem eigenen Import; unbekannte Angaben wurden nicht ergänzt."
            if cur.src.profile == "imported"
            else "Bibliografische Angaben aus Colibri; Abgleich mit METS/MODS im Reiter „Bibliotheksdaten“."
        )
        ui.section("Seite")
        label = source.get("page_label_mets")
        st.markdown(
            f"Scan {source['scan_number']} im Digitalisat"
            + (f" ({source['physical_page_id']})" if source["physical_page_id"] else "")
            + "  \n"
            + (
                f"Seitenbezeichnung im METS: „{label}“; gedruckte Seitenzahl am Scan noch nicht bestätigt"
                if label
                else "Gedruckte Seitenzahl unbekannt; Scan-Nummer ist keine Seitenzahl"
            )
        )
        if source["viewer_url"]:
            st.link_button(
                "Originalansicht der Staatsbibliothek öffnen",
                source["viewer_url"],
                icon=":material/open_in_new:",
            )
        ui.section("Bildbeschreibung")
        ui.source_text(record["image_description"]["working_description_de"])
        ui.status_badge(record["image_description"]["review_status"])
        ui.section("Rechte und Herkunft")
        if cur.src.profile == "imported":
            st.write("Quelle:", source["institution"] or "unbekannt")
            st.write("Rechte:", biblio["rights_statement"] or "unbekannt")
        else:
            st.markdown(
                f"Quellwerk: {biblio['rights_statement']}  \n"
                f"Colibri-Datensatz: [CC BY 4.0]({source['colibri_dataset_license']}) – "
                f"{source['colibri_dataset_credit']}"
            )
        if source.get("colibri_groundtruth"):
            st.caption(
                f"Colibri-Annotation dieser Abbildung: manuell „{source['colibri_groundtruth']}“, "
                f"automatisch „{source['colibri_classification']}“."
            )

    progress_table(record)
    if "working_publisher_statement" in (record.get("transcription") or {}):
        imprint_comparison(record)
    ui.section("Fachliche Hinweise")
    with st.container(border=True):
        for item in record["review_items"]:
            st.markdown(f"- {item['note_de']}")
    with st.expander("Technische Angaben"):
        st.text(
            f"Objekt-ID: {record['id']}\nPPN: {source['ppn']}\n"
            f"Colibri-Datei: {source['colibri_file_reference']}\nBildinfo (IIIF): {source['image_info_url']}\n"
            f"Quelldatei (nur gelesen): {cur.working['based_on']['file']}\n"
            f"Arbeitskopie: {store.work_path(record['id']).relative_to(store.DATA_DIR)}"
        )


def progress_table(record: dict) -> None:
    areas = review.review_areas(record)
    ui.section(
        f"Prüfbereiche: {sum(a['done'] for a in areas)} von {len(areas)} bestätigt"
    )
    st.dataframe(
        [
            {
                "Stand": "Bestätigt" if a["done"] else "Offen",
                "Bereich": a["label_de"],
                "Prüfstand": review.status_label(a["status"]),
                "Reiter": a["tab_de"],
            }
            for a in areas
        ],
        hide_index=True,
    )


def imprint_comparison(record: dict) -> None:
    biblio = record["bibliographic_metadata_from_colibri"]
    ui.section("Verlagsangaben im Vergleich")
    left, right = st.columns(2)
    with left, st.container(border=True):
        ui.subsection("Bibliografische Angabe (Colibri, MODS)")
        st.text(
            f"Ort: {biblio['publication_place'] or 'unbekannt'}\n"
            f"Verlag: {biblio['publisher'] or 'unbekannt'}"
        )
    with right, st.container(border=True):
        ui.subsection("Aufdruck auf dem Bildblatt (vorläufige Lesung)")
        ui.source_text(record["transcription"]["working_publisher_statement"])
        ui.status_badge(
            record["transcription"]["review_status_by_field"][
                "working_publisher_statement"
            ]
        )
    st.caption(
        "Beide Angaben bleiben mit ihrem Bezug erhalten. Die Abweichung wird zur Prüfung angezeigt, "
        "nicht als Katalogfehler gewertet und nicht angeglichen."
    )


def region_option(record: dict, region: dict) -> str:
    # Feste Beschriftung: ändert sich der Text (z. B. Status), verliert das Frontend die Auswahl
    return f"{record['region_annotations'].index(region) + 1} · {region['label_de']}"


def region_tab(cur: Current) -> None:
    record = cur.record
    by_id = {r["id"]: r for r in record["region_annotations"]}
    choice = next(iter(by_id))
    if len(by_id) > 1:
        choice = st.radio(
            "Region auswählen",
            list(by_id),
            format_func=lambda i: region_option(record, by_id[i]),
            horizontal=True,
            key=f"{cur.id}-region-choice",
        )
    canvas_section(cur)
    withdrawn_regions_list(cur)
    left, right = ui.image_and_controls(pinned="regionen")
    with right:
        preview_xywh = region_editor(cur, by_id[choice])
    with left:
        preview = [
            {**r, "xywh": preview_xywh} if r["id"] == choice else r
            for r in record["region_annotations"]
        ]
        st.image(
            regions.draw_regions(ui.page_image(cur.src.page_image), preview),
            width="stretch",
            caption="Gesamtseite; die gewählte Region mit den aktuell eingegebenen Werten",
            alt="Gescannte Buchseite; die Regionen sind als nummerierte Rahmen markiert, die gewählte mit den eingegebenen Werten.",
        )
    width, height = cur.size
    st.caption(
        f"Koordinaten sind Pixel [x, y, Breite, Höhe] im Ausgangsbild {width} × {height}, gezählt ab der "
        "linken oberen Ecke. Die verkleinerte Anzeige ändert sie nicht."
    )


CANVAS_TYPES = {"illustration": "Illustration", "text": "Text"}


def canvas_section(cur: Current) -> None:
    object_id = cur.id
    draft_key = actions.draft_key(object_id)
    draft = st.session_state.get(draft_key) or {
        "changes": {},
        "base": {},
        "created": None,
    }
    revision = st.session_state.get(f"{object_id}-canvas-rev", 0)
    instance = f"{object_id}-canvas-{revision}"
    saved = cur.record["region_annotations"]
    error = None
    try:
        event = region_canvas.pending_event(
            instance, {r["id"] for r in saved}, *cur.size
        )
    except ValueError as exc:
        error, event = str(exc), None
    seq_key = f"{object_id}-canvas-seq"
    if event and event["seq"] != st.session_state.get(seq_key):
        st.session_state[seq_key] = event["seq"]
        base = draft["base"] or {r["id"]: r["xywh"] for r in saved}
        draft = {"changes": event["changes"], "base": base, "created": event["created"]}
        st.session_state[draft_key] = draft
        if event["created"]:
            ui.load_fields(new_region_keys(object_id), event["created"]["xywh"])
            st.session_state[f"{object_id}-new-type"] = event["created"]["type"]
    shown = [
        {
            "id": r["id"],
            "label": r["label_de"],
            "type": r["region_type"],
            "saved": r["xywh"],
            "xywh": draft["changes"].get(r["id"], r["xywh"]),
        }
        for r in saved
    ]
    ui.section("Auf dem Scan zeichnen und verschieben")
    st.caption(
        "Rahmen ziehen oder an den Ecken ändern; Umschalt+Klick wählt mehrere. Nichts wird gespeichert, "
        "bevor Sie unten ausdrücklich speichern. Alternativ: Zahlenfelder unter „Rahmen korrigieren“."
    )
    if error:
        st.error(error, icon=ui.ERROR)
    region_canvas.render(
        instance, cur.src.page_image, cur.size, shown, draft["created"]
    )
    if draft["changes"]:
        st.dataframe(
            [
                {
                    "Region": r["label_de"],
                    "Gespeichert": str(r["xywh"]),
                    "Entwurf": str(draft["changes"][r["id"]]),
                }
                for r in saved
                if r["id"] in draft["changes"]
            ],
            hide_index=True,
        )
        buttons = st.columns(2)
        buttons[0].button(
            "Verschiebungen speichern (Entwurf)",
            key=f"{object_id}-canvas-save",
            on_click=actions.save_canvas_draft,
            args=(object_id,),
        )
        buttons[1].button(
            "Verschiebungen verwerfen",
            key=f"{object_id}-canvas-discard",
            on_click=actions.bump_canvas,
            args=(object_id,),
        )
    ui.feedback(object_id, "canvas-save")
    new_region_form(cur, draft)


def new_region_keys(object_id: str) -> list[str]:
    return [f"{object_id}-new-{k}" for k in "xywh"]


def new_region_form(cur: Current, draft: dict) -> None:
    object_id = cur.id
    keys = new_region_keys(object_id)
    width, height = cur.size
    if keys[0] not in st.session_state:
        ui.load_fields(keys, [0, 0, min(100, width), min(100, height)])
    with st.expander("Neue Region anlegen", expanded=bool(draft["created"])):
        kind = st.radio(
            "Typ",
            list(CANVAS_TYPES),
            format_func=CANVAS_TYPES.get,
            horizontal=True,
            key=f"{object_id}-new-type",
        )
        label = st.text_input("Bezeichnung", key=f"{object_id}-new-label")
        cols = st.columns(4)
        for col, key, name in zip(
            cols, keys, ["x (links)", "y (oben)", "Breite", "Höhe"]
        ):
            col.number_input(name, step=1, key=key)
        xywh = [int(st.session_state[key]) for key in keys]
        problems = regions.bounds_problems(xywh, width, height)
        for problem in problems:
            st.error(problem, icon=ui.ERROR)
        st.button(
            "Neue Region anlegen (Entwurf)",
            key=f"{object_id}-new-save",
            on_click=actions.add_region,
            args=(object_id, kind, label, xywh, len(cur.record["region_annotations"])),
            disabled=bool(problems) or not label.strip(),
        )
        ui.feedback(object_id, "canvas-add")


def region_editor(cur: Current, region: dict) -> list[int]:
    """Bearbeitung einer Region; liefert die für die Vorschau gültigen Koordinaten."""
    region_id = region["id"]
    width, height = cur.size
    ui.section(f"Region {region_option(cur.record, region)}")
    ui.status_badge(region["review_status"])
    keys = actions.xywh_keys(region_id)
    sync = ui.sync_fields(keys, region["xywh"])
    if region["review_status"] == review.REGION_REVIEWED:
        ui.confirmed_note(cur.record, region_id)
        if sync == ui.CLEAN:
            region_continue(cur, region_id)
    else:
        st.markdown(
            "**Prüfen Sie den markierten Rahmen im Scan.** Passt er genau um den Bereich, "
            "setzen Sie das Häkchen und speichern Sie die Prüfung."
        )
        ui.confirm_controls(
            f"{region_id}-review",
            "Ihre Bestätigung gilt für die gespeicherten Grenzen.",
            "Der Rahmen erfasst den Bereich vollständig.",
            actions.confirm_region,
            (cur.id, region_id, region["xywh"]),
            blocked_de="Speichern oder verwerfen Sie zuerst Ihre Änderungen unter „Rahmen korrigieren“."
            if sync != ui.CLEAN
            else None,
            button_label="Rahmen als geprüft bestätigen",
        )
    # Fester Schlüssel: sonst klappt der Bereich zu, sobald die Eingabe wieder dem Gespeicherten entspricht
    with st.expander(
        "Rahmen korrigieren", expanded=sync != ui.CLEAN, key=f"{region_id}-correct"
    ):
        ui.origin_note(region.get("region_origin_de"))
        shown = region_coordinates(cur, region, keys, sync, width, height)
    st.image(
        regions.crop(ui.page_image(cur.src.page_image), shown),
        width=ui.crop_width(shown),
        caption="Ausschnitt mit den eingegebenen Werten"
        if sync != ui.CLEAN
        else "Ausschnitt (gespeicherter Stand)",
        alt="Ausschnitt der gewählten Region aus der gescannten Seite.",
    )
    if review.is_imported(cur.record):
        withdraw_region_form(cur, region)
    return shown


def withdraw_region_form(cur: Current, region: dict) -> None:
    key = f"{region['id']}-withdraw"
    only = len(cur.record["region_annotations"]) < 2
    with st.expander("Region zurückziehen", key=f"{key}-box"):
        st.caption(
            "Die Region verschwindet aus der Arbeit, bleibt aber mit Ihrem Namen, der Zeit und dem "
            "Grund im Datensatz, im Verlauf und im JSON-Export erhalten. Eine zugehörige "
            "Transkription wird mitgenommen. Die Endbestätigung wird aufgehoben, der Export veraltet."
        )
        if only:
            st.info("Die letzte Region kann nicht zurückgezogen werden.", icon=ui.INFO)
        st.text_input("Grund", key=f"{key}-reason", disabled=only)
        st.button(
            "Region zurückziehen",
            key=f"{key}-submit",
            on_click=actions.withdraw_region,
            args=(cur.id, region["id"], region["xywh"]),
            disabled=only,
        )
        if error := st.session_state.pop(f"{key}-error", None):
            st.error(error, icon=ui.ERROR)


def withdrawn_regions_list(cur: Current) -> None:
    entries = cur.record.get("withdrawn_regions", [])
    if not entries:
        return
    with st.expander(f"Zurückgezogene Regionen ({len(entries)})"):
        for e in entries:
            st.markdown(
                f"- {e['region']['label_de']} ({e['region']['id']}), {e['region']['xywh']}: "
                f"{e['reason']} (zurückgezogen von {e['by']}, {ui.local_time(e['at'])})"
            )


def region_coordinates(
    cur: Current, region: dict, keys: list[str], sync: str, width: int, height: int
) -> list[int]:
    region_id = region["id"]
    cols = st.columns(4)
    # Ohne Feldgrenzen: Werte außerhalb des Bildes meldet bounds_problems auf Deutsch
    for col, key, label in zip(cols, keys, ["x (links)", "y (oben)", "Breite", "Höhe"]):
        col.number_input(label, step=1, key=key)
    xywh = actions.input_xywh(region_id)
    problems = regions.bounds_problems(xywh, width, height)
    for problem in problems:
        st.error(problem, icon=ui.ERROR)
    if sync == ui.CONFLICT:
        ui.conflict_note(keys, region["xywh"], str(region["xywh"]))
    ui.edit_state(
        sync,
        f"Gespeichert ist {region['xywh']}. Speichern setzt den Prüfstand dieser Region zurück.",
    )
    buttons = st.columns(2)
    buttons[0].button(
        "Rahmen speichern (Entwurf)",
        key=f"{region_id}-save",
        on_click=actions.save_coordinates,
        args=(cur.id, region_id),
        disabled=sync != ui.EDITED or bool(problems),
    )
    buttons[1].button(
        "Eingaben verwerfen",
        key=f"{region_id}-discard",
        on_click=ui.load_fields,
        args=(keys, region["xywh"]),
        disabled=sync != ui.EDITED,
    )
    if sync == ui.CLEAN:
        ui.feedback(cur.id, f"{region_id}-save")

    return region["xywh"] if problems else xywh


def region_continue(cur: Current, region_id: str) -> None:
    pending = next(
        (
            region
            for region in cur.record["region_annotations"]
            if region["review_status"] != review.REGION_REVIEWED
        ),
        None,
    )
    if pending is None:
        workflow.continue_button(cur.id, cur.record, f"{region_id}-continue")
        return
    st.button(
        f"Weiter: nächsten Rahmen prüfen ({pending['label_de']})",
        key=f"{region_id}-continue",
        type="primary",
        icon=":material/arrow_forward:",
        on_click=st.session_state.update,
        args=({f"{cur.id}-region-choice": pending["id"]},),
    )


def tab_continue(cur: Current, tab: str) -> None:
    """Sind alle Prüfbereiche dieses Reiters bestätigt, führt „Weiter“ zum nächsten Schritt."""
    if all(a["done"] for a in review.review_areas(cur.record) if a["tab_de"] == tab):
        st.success(f"Alle Bereiche in „{tab}“ sind bestätigt.", icon=ui.CONFIRMED)
        workflow.continue_button(cur.id, cur.record, f"{cur.id}-{tab.lower()}-continue")


def description_tab(cur: Current) -> None:
    illustration = next(
        (
            r
            for r in cur.record["region_annotations"]
            if r["region_type"] == "illustration"
        ),
        None,
    )
    left, right = ui.image_and_controls(pinned="beschreibung")
    with left:
        if illustration:
            st.image(
                regions.crop(ui.page_image(cur.src.page_image), illustration["xywh"]),
                width="stretch",
                caption="Ausschnitt der Illustration (gespeicherte Grenzen)",
                alt="Ausschnitt der Illustration aus der gescannten Seite.",
            )
    with right:
        description_editor(cur)
        for region in cur.record["region_annotations"]:
            if "keywords_de" in region:
                st.divider()
                keyword_editor(cur, region)
        tab_continue(cur, "Beschreibung")


def biblio_tab(cur: Current) -> None:
    record = cur.record
    stored_values = review.biblio_values(record)
    ui.section("Bibliografische Angaben")
    st.badge(
        review.status_label(record.get("biblio_review_status", review.BIBLIO_OPEN)),
    )
    st.caption(
        "Eigene Eingabe, nicht aus Colibri/MODS. Ein leeres Feld gilt als unbekannt. "
        "Der Buchtitel bleibt, wie importiert."
    )
    keys = actions.biblio_keys(cur.id)
    stored = [stored_values[name] or "" for name in review.BIBLIO_FIELDS]
    sync = ui.sync_fields(keys, stored, lambda values: [v.strip() for v in values])
    for key, (label, _, _) in zip(keys, review.BIBLIO_FIELDS.values()):
        st.text_input(label, key=key)
    if sync == ui.CONFLICT:
        ui.conflict_note(keys, stored, "siehe gespeicherte Angaben")
    ui.edit_state(sync, "Speichern setzt die Bestätigung der Angaben zurück.")
    save_key = f"{cur.id}-biblio-save"
    st.button(
        "Angaben speichern (Entwurf)",
        key=save_key,
        on_click=actions.save_biblio,
        args=(cur.id,),
        disabled=sync != ui.EDITED,
    )
    if sync == ui.CLEAN:
        ui.feedback(cur.id, save_key)
    if record.get("biblio_review_status") == review.BIBLIO_REVIEWED:
        ui.confirmed_note(record, "bibliographic")
    else:
        ui.confirm_controls(
            f"{cur.id}-biblio-review",
            "Die gespeicherten Angaben stimmen mit dem Buch überein.",
            "Ich habe die Angaben am Buch geprüft.",
            actions.confirm_biblio,
            (cur.id, stored_values),
            blocked_de="Erst die Eingabe speichern oder verwerfen."
            if sync != ui.CLEAN
            else None,
        )
    tab_continue(cur, "Angaben")


def description_editor(cur: Current) -> None:
    description = cur.record["image_description"]
    ui.section("Bildbeschreibung")
    ui.status_badge(description["review_status"])
    ui.origin_note(description.get("description_origin_de"))
    st.caption(
        f"Objektart: {description['object_type']} · Illustrator: "
        f"{description['illustrator'] or 'unbekannt'} (Buchautor und Illustrator sind "
        "verschiedene Rollen)"
    )
    key, stored = actions.description_key(cur.id), description["working_description_de"]
    sync = ui.sync_fields([key], [stored], lambda values: [values[0].strip()])
    st.text_area(
        "Bildbeschreibung (sichtbarer Inhalt, ohne Deutung)",
        key=key,
        height=ui.TEXT_AREA_HEIGHT,
    )
    if sync == ui.CONFLICT:
        ui.conflict_note([key], [stored], f"„{stored}“")
    ui.edit_state(sync, "Speichern setzt die Bestätigung der Beschreibung zurück.")
    st.button(
        "Text speichern (Entwurf)",
        key=f"{key}-save",
        on_click=actions.save_description,
        args=(cur.id,),
        disabled=sync != ui.EDITED,
    )
    if sync == ui.CLEAN:
        ui.feedback(cur.id, f"{key}-save")
    if description["observation_de"] != stored:
        with st.expander("Erste Beobachtung (unverändert)"):
            ui.source_text(description["observation_de"])
    if description["review_status"] == review.DESCRIPTION_REVIEWED:
        ui.confirmed_note(cur.record, "image_description")
    else:
        ui.confirm_controls(
            f"{key}-review",
            "Die gespeicherte Beschreibung gibt den sichtbaren Bildinhalt zutreffend wieder.",
            "Ich habe die Beschreibung am Bild geprüft.",
            actions.confirm_description,
            (cur.id, stored),
            blocked_de="Erst die Eingabe speichern oder verwerfen."
            if sync != ui.CLEAN
            else None,
        )


def keyword_editor(cur: Current, region: dict) -> None:
    region_id = region["id"]
    ui.section(f"Suchbegriffe: {region['label_de']}")
    ui.status_badge(region["keyword_review_status"])
    ui.origin_note(region.get("keyword_origin_de"))
    st.caption("Projektlokale Begriffe, keine geprüften GND-Verknüpfungen.")
    key, stored = actions.keyword_key(region_id), ["\n".join(region["keywords_de"])]
    sync = ui.sync_fields(
        [key], stored, lambda values: [actions.keyword_list(values[0])]
    )
    st.text_area("Ein Begriff pro Zeile", key=key, height=ui.TEXT_AREA_HEIGHT)
    if sync == ui.CONFLICT:
        ui.conflict_note([key], stored, "; ".join(region["keywords_de"]))
    ui.edit_state(sync, "Speichern setzt die Bestätigung der Suchbegriffe zurück.")
    st.button(
        "Begriffe speichern (Entwurf)",
        key=f"{key}-save",
        on_click=actions.save_keywords,
        args=(cur.id, region_id),
        disabled=sync != ui.EDITED,
    )
    if sync == ui.CLEAN:
        ui.feedback(cur.id, f"{key}-save")
    if region["keyword_review_status"] == review.KEYWORDS_ACCEPTED:
        ui.confirmed_note(cur.record, f"{region_id}/keywords_de")
    else:
        ui.confirm_controls(
            f"{key}-review",
            "Die gespeicherten Begriffe beschreiben den Bildinhalt zutreffend.",
            "Ich habe die Suchbegriffe am Bild geprüft.",
            actions.confirm_keywords,
            (cur.id, region_id, region["keywords_de"]),
            blocked_de="Erst die Eingabe speichern oder verwerfen."
            if sync != ui.CLEAN
            else None,
        )


def transcription_tab(cur: Current) -> None:
    transcription = cur.record["transcription"]
    ui.neutral_badge("Keine Ground Truth")
    st.caption(
        "Ground Truth wäre eine freigegebene Referenztranskription, an der OCR gemessen wird "
        "(CER/WER). Die gibt es hier nicht; die OCR-Ausgabe wird deshalb gezeigt, nicht bewertet. "
        "Prüfweg: Bildausschnitt ansehen, Arbeitstranskription Zeichen für Zeichen vergleichen, "
        "historische Schreibweise beibehalten, dann bestätigen oder vorläufig lassen."
    )
    st.caption(
        f"{transcription['review_note_de']} Bildtitel und Verlagsangabe werden einzeln geprüft."
    )
    ocr = cur.record.get("ocr_result")
    for region in cur.record["region_annotations"]:
        if region.get("transcription_field"):
            with st.container(border=True):
                transcription_editor(
                    cur,
                    region,
                    ocr if ocr and ocr["region_id"] == region["id"] else None,
                )
    tab_continue(cur, "Transkription")
    with st.expander("Erste Lesung (unverändert, mit Zeilenumbruch)"):
        st.code(transcription["initial_user_transcription"], language=None)


def transcription_editor(cur: Current, region: dict, ocr: dict | None) -> None:
    transcription = cur.record["transcription"]
    field = region["transcription_field"]
    status = transcription["review_status_by_field"][field]
    ui.section(f"{region['label_de']}")
    ui.status_badge(status)
    st.image(
        regions.crop(ui.page_image(cur.src.page_image), region["xywh"]),
        width=ui.crop_width(region["xywh"]),
        caption="Vorlage: Ausschnitt aus dem Scan",
        alt=f"Ausschnitt mit dem Text für: {region['label_de']}.",
    )
    key = actions.transcription_key(cur.id, field)
    sync = ui.sync_fields([key], [transcription[field]])
    columns = st.columns(2 if ocr else 1, gap="large")
    with columns[0]:
        st.text_input(
            "Arbeitstranskription (zeichengetreu, historische Schreibweise beibehalten)",
            key=key,
        )
        if sync == ui.CONFLICT:
            ui.conflict_note([key], [transcription[field]], f"„{transcription[field]}“")
        ui.edit_state(
            sync, "Speichern setzt nur den Prüfstand dieses Textes auf „vorläufig“."
        )
        st.button(
            "Lesung speichern (Entwurf)",
            key=f"{key}-save",
            on_click=actions.save_transcription,
            args=(cur.id, field),
            disabled=sync != ui.EDITED,
        )
        if sync == ui.CLEAN:
            ui.feedback(cur.id, f"{key}-save")
    if ocr:
        with columns[1]:
            ocr_block(cur, ocr)
    second_reading(cur, region, transcription[field], ocr)
    if status == review.TRANSCRIPTION_REVIEWED:
        ui.confirmed_note(cur.record, f"transcription/{field}")
    else:
        ui.confirm_controls(
            f"{key}-review",
            f"Die gespeicherte Lesung „{region['label_de']}“ stimmt mit der Vorlage überein. "
            "Das ist keine Freigabe als Ground Truth.",
            "Ich habe diesen Text an der Vorlage geprüft.",
            actions.confirm_transcription,
            (cur.id, field, transcription[field]),
            blocked_de="Erst die Eingabe speichern oder verwerfen."
            if sync != ui.CLEAN
            else None,
        )


def diff_markdown(before: str, after: str) -> str:
    marks = {"gleich": "{}", "entfernt": "~~{}~~", "hinzugefügt": "**+{}+**"}
    return " ".join(
        marks[kind].format(text.replace("\n", "⏎"))
        for kind, text in ocr.text_diff(before, after)
    )


def second_reading(
    cur: Current, region: dict, human: str, original: dict | None
) -> None:
    region_id, field = region["id"], region["transcription_field"]
    key = actions.ocr_run_key(cur.id, region_id)
    with st.expander(
        "Zweite Lesung mit lokaler OCR (Tesseract)", key=f"{key}-expander"
    ):
        st.caption(
            "Läuft nur auf Ihren Knopfdruck auf diesem Rechner; das Bild verlässt ihn nicht. "
            "Das Ergebnis ist keine bewertete oder genauere Lesung, nur ein weiterer Vergleichstext."
        )
        try:
            models = ocr.available_models()
        except ocr.OcrUnavailable as error:
            st.info(str(error), icon=ui.INFO)
            return
        if not models:
            st.info(
                "Keine Tesseract-Modelle installiert; die manuelle Transkription bleibt nutzbar."
            )
            return
        model = st.selectbox("Modell", models, key=f"{key}-model")
        psm = st.radio(
            "Modus",
            list(ocr.MODES),
            format_func=ocr.MODES.get,
            horizontal=True,
            key=f"{key}-psm",
        )
        st.button(
            "Lokale OCR jetzt ausführen",
            key=f"{key}-run",
            on_click=actions.run_ocr,
            args=(cur.id, region_id, model, psm),
        )
        if message := st.session_state.get(f"{key}-error"):
            st.error(message, icon=ui.ERROR)
        run = st.session_state.get(key)
        if run and run["xywh"] == region["xywh"]:
            show_candidate(cur, region, human, original, run)
            st.button(
                "Lesung als Kandidat speichern",
                key=f"{key}-save",
                on_click=actions.save_ocr,
                args=(cur.id, region_id),
            )
            ui.feedback(cur.id, f"{key}-save")
        saved = [
            c
            for c in cur.record.get("ocr_candidates", [])
            if c["region_id"] == region_id
        ]
        if saved:
            crop_sha = actions.current_crop_sha(cur.src, region)
            ui.subsection("Gespeicherte zweite Lesungen")
        for candidate in saved:
            stale = review.candidate_stale(candidate, region, crop_sha)
            with st.container(border=True):
                st.code(candidate["text"], language=None)
                st.caption(
                    f"{candidate['engine_version']}, Modell {candidate['model']} "
                    f"(SHA-256 {str(candidate['model_sha256'])[:12]}), PSM {candidate['psm']}, "
                    f"{ui.local_time(candidate['created_at'])}"
                    + (
                        "; veraltet: der Bildausschnitt wurde seither geändert"
                        if stale
                        else ""
                    )
                )
                st.markdown(
                    "Gegenüber Ihrer Arbeitstranskription: "
                    + diff_markdown(human, candidate["text"])
                )
                st.button(
                    "Als Entwurf in die Transkription übernehmen",
                    key=f"{key}-adopt-{candidate['id']}",
                    on_click=actions.adopt_ocr,
                    args=(cur.id, region_id, candidate["id"], field),
                    disabled=stale,
                    help="Ändert nur das Eingabefeld und speichert als Entwurf; bestätigt wird nichts.",
                )


def show_candidate(
    cur: Current, region: dict, human: str, original: dict | None, run: dict
) -> None:
    ui.subsection("Neue Lesung (noch nicht gespeichert)")
    st.code(run["text"], language=None)
    st.markdown(
        "Gegenüber Ihrer Arbeitstranskription: " + diff_markdown(human, run["text"])
    )
    if original:
        st.markdown(
            "Gegenüber der unveränderten Quell-OCR: "
            + diff_markdown(original["raw_text"], run["text"])
        )
    st.caption(
        "Durchgestrichen: nur in der Vergleichsbasis; fett mit +: nur in der neuen Lesung."
    )


def ocr_block(cur: Current, ocr: dict) -> None:
    meta = store.read_json(cur.src.record.parent / ocr["result_file"])
    ui.subsection("Gespeicherte OCR-Ausgabe (unverändert, ungeprüft)")
    st.code(ocr["raw_text"], language=None)
    st.caption(
        f"{meta['engine_version']}, Modell {meta['language_model']}, ohne Vorverarbeitung. "
        "Ein einzelner Versuch, keine Bewertung der OCR-Qualität."
    )
    with st.expander("Technische Angaben zum OCR-Lauf"):
        st.text(
            f"Genaue Zeichenfolge: {ocr['raw_text']!r} ({len(ocr['raw_text'])} Zeichen)\n"
            f"Modellrevision {meta['model_revision']}\n"
            f"OEM {meta['engine_mode']}, PSM {meta['page_segmentation_mode']}, "
            f"Vorverarbeitung: {meta['preprocessing']}\n"
            f"Eingabebild: {meta['input_file']} (SHA-256 {meta['input_sha256'][:16]}…)"
        )
