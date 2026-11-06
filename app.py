"""Kinderbuch-Bildlabor: Prüfoberfläche für ein Pilotobjekt.

Start: uv run streamlit run app.py
Arbeitet nur mit den gespeicherten Dateien im Startpaket; kein Netzabruf, keine OCR.
"""

import csv

import streamlit as st
from PIL import Image

from kinderbuch_bildlabor import export, library_view, regions, review, store, ui, validate

st.set_page_config(page_title="Kinderbuch-Bildlabor", layout="wide")


@st.cache_resource
def page_image() -> Image.Image:
    """Das Ausgangsbild ist unveränderlich; nur Arbeitsdaten werden bei jedem Lauf neu gelesen."""
    return Image.open(store.PAGE_IMAGE).convert("RGB")


# Bei jedem Lauf frisch von der Platte: ein anderer Tab kann inzwischen gespeichert haben
working = store.load_working_copy()
record = working["record"]
source = record["source"]
WIDTH, HEIGHT = source["image_width"], source["image_height"]
JSON_EXPORT = store.EXPORT_DIR / f"{record['id']}.json"
CSV_EXPORT = store.EXPORT_DIR / f"{record['id']}.csv"


def reviewer() -> str:
    return st.session_state.get("reviewer", "").strip()


# --- Aktionen: jede liest den gespeicherten Stand, ändert ihn und speichert nur echte Änderungen

def apply(area_de: str, change, *args) -> None:
    current = store.load_working_copy()
    try:
        changed = change(current["record"], *args)
    except review.ContentChanged as error:
        st.session_state.notice = str(error)
        return
    if not changed:
        st.toast(f"Nichts gespeichert: {area_de} entspricht bereits dem gespeicherten Stand.",
                 icon=":material/info:")
        return
    store.save_working_copy(current, area_de)
    st.toast(f"Gespeichert: {area_de}", icon=":material/check:")


def input_xywh(region_id: str) -> list[int]:
    return [int(st.session_state[f"{region_id}-{k}"]) for k in "xywh"]


def save_coordinates(region_id: str) -> None:
    apply(f"Koordinaten {region_id}", review.set_region_xywh, region_id, input_xywh(region_id))


def discard_coordinates(region_id: str, saved_xywh: list[int]) -> None:
    for key, value in zip("xywh", saved_xywh):
        st.session_state[f"{region_id}-{key}"] = value


def confirm_region(region_id: str, seen_xywh: list[int]) -> None:
    apply(f"Bestätigung Regionsgrenzen {region_id}", review.confirm_region, region_id, reviewer(), seen_xywh)


def keyword_input(region_id: str) -> list[str]:
    lines = st.session_state[f"{region_id}-keywords"].splitlines()
    return [line.strip() for line in lines if line.strip()]


def save_keywords(region_id: str) -> None:
    apply(f"Suchbegriffe {region_id}", review.set_keywords, region_id, keyword_input(region_id))


def confirm_keywords(region_id: str, seen: list[str]) -> None:
    apply(f"Bestätigung Suchbegriffe {region_id}", review.confirm_keywords, region_id, reviewer(), seen)


def save_description() -> None:
    apply("Arbeitsbeschreibung", review.set_description, st.session_state["description"].strip())


def save_transcription(field: str) -> None:
    apply(f"Transkription {field}", review.set_transcription, field, st.session_state[field])


def confirm_transcription(field: str, seen_text: str) -> None:
    apply(f"Bestätigung Transkription {field}", review.confirm_transcription, field, reviewer(), seen_text)


def run_export() -> None:
    current = store.load_working_copy()
    data = export.export_json(current, JSON_EXPORT)
    export.export_csv(current["record"], data["exported_at"], CSV_EXPORT)
    st.session_state.pop("roundtrip_result", None)
    st.toast("Exportiert: JSON und CSV", icon=":material/check:")


def run_roundtrip() -> None:
    exported = store.read_json(JSON_EXPORT)
    current = store.load_working_copy()
    st.session_state.roundtrip_result = (exported["exported_at"],
                                         export.roundtrip_report(current["record"], exported["record"]),
                                         export.differing_fields(current["record"], exported["record"]))


# --- Ansichten ----------------------------------------------------------------------------

def sidebar() -> None:
    st.sidebar.header("Arbeitsstand")
    st.sidebar.text_input("Prüfende Person", key="reviewer",
                          help="Wird bei jeder ausdrücklichen Bestätigung mit Zeitpunkt gespeichert.")
    st.sidebar.write(f"Objekt: `{record['id']}` · {review.status_label(record['status'])}")
    if working["change_log"]:
        st.sidebar.write(f"Zuletzt gespeichert: {ui.local_time(working['change_log'][-1]['saved_at'])}")
    else:
        st.sidebar.write("Noch nichts gespeichert. Angezeigt wird die unveränderte Quelldatei.")
    st.sidebar.caption(f"Quelle (nur gelesen): {working['based_on']['file']}  \n"
                       f"Arbeitskopie: data/work/{record['id']}.json")


def export_state() -> tuple[str, list[dict] | None, dict | None]:
    """'none', 'current', 'stale' oder 'foreign' mit späteren Änderungen und Exportdaten."""
    if not JSON_EXPORT.exists():
        return "none", None, None
    exported = store.read_json(JSON_EXPORT)
    later = export.later_changes(working, exported)
    state = "foreign" if later is None else "stale" if later else "current"
    return state, later, exported


def progress_overview() -> None:
    areas = review.review_areas(record)
    done = sum(a["done"] for a in areas)
    st.markdown(f"#### Prüfbereiche: {done} von {len(areas)} bestätigt")
    rows = "\n".join(f"| {'Erledigt' if a['done'] else 'Offen'} | {a['label_de']} | "
                     f"{review.status_label(a['status'])} | {a['tab_de']} |" for a in areas)
    st.markdown("| Stand | Bereich | Prüfstand | Reiter |\n|---|---|---|---|\n" + rows)
    open_areas = [a for a in areas if not a["done"]]
    if open_areas:
        step = f"{open_areas[0]['label_de']} prüfen (Reiter „{open_areas[0]['tab_de']}“)."
    elif export_state()[0] != "current":
        step = "Export erstellen (Reiter „Export“)."
    else:
        step = "Alle Einzelbereiche bestätigt; die Endprüfung des Objekts steht noch aus."
    st.info(f"Nächster sinnvoller Schritt: {step}", icon=":material/arrow_forward:")


def overview_tab() -> None:
    biblio = record["bibliographic_metadata_from_colibri"]
    st.subheader(biblio["title"])
    st.write(f"{source['institution']} · {source['ppn']} · {source['physical_page_id']} "
             f"(Scan {source['scan_number']}; gedruckte Seitenzahl unbekannt)")
    st.link_button("Originalansicht der Staatsbibliothek öffnen", source["viewer_url"],
                   icon=":material/open_in_new:")
    progress_overview()

    st.markdown("#### Verlagsangaben im Vergleich")
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("**Laut Colibri (bibliografische Angaben)**")
        st.text(f"Verfasser: {biblio['author_display']}\nOrt: {biblio['publication_place']}\n"
                f"Verlag: {biblio['publisher']}\nJahr: {biblio['publication_date']}")
    with right, st.container(border=True):
        st.markdown("**Auf dem Bildblatt (vorläufige Lesung)**")
        ui.source_text(record["transcription"]["working_publisher_statement"])
        ui.status_badge(record["transcription"]["review_status_by_field"]["working_publisher_statement"])
    st.caption("Beide Angaben bleiben mit ihrem Bezug erhalten. Die Abweichung wird zur Prüfung angezeigt "
               "und nicht als Katalogfehler gewertet.")

    st.markdown("#### Bildbeschreibung")
    description = record["image_description"]
    st.write(f"Objektart: {description['object_type']}")
    ui.source_text(description["working_description_de"])
    st.write("Illustrator: unbekannt (bewusst leer; Buchautor und Illustrator sind verschiedene Rollen)")

    st.markdown("#### Offene Prüfhinweise")
    for item in record["review_items"]:
        st.warning(f"{item['note_de']}  \nCode: {item['code']}")

    st.markdown("#### Rechte und Herkunft")
    st.write(f"Quellwerk: {biblio['rights_statement']}  \n"
             f"Colibri-Datensatz: Lizenz {source['colibri_dataset_license']}  \n"
             f"Namensnennung: {source['colibri_dataset_credit']}")
    with st.expander("Technische Quellbezüge"):
        st.text(f"Colibri-Datei: {source['colibri_file_reference']}\nBildinfo (IIIF): {source['image_info_url']}")


def region_option(region: dict) -> str:
    # Feste Beschriftung: ändert sich der Text (z. B. Status), verliert das Frontend die Auswahl
    return f"{record['region_annotations'].index(region) + 1} · {region['label_de']}"


def region_tab() -> None:
    by_id = {r["id"]: r for r in record["region_annotations"]}
    choice = st.radio("Region auswählen", list(by_id), format_func=lambda i: region_option(by_id[i]),
                      horizontal=True, key="region-choice")
    left, right = st.columns([2, 3], gap="large")
    with right:
        preview_xywh = region_editor(by_id[choice])
    with left:
        preview = [{**r, "xywh": preview_xywh} if r["id"] == choice else r for r in record["region_annotations"]]
        st.image(regions.draw_regions(page_image(), preview), width="stretch",
                 caption=f"Gesamtansicht; Region {choice} mit den aktuell eingegebenen Werten")
    st.caption(f"Alle Koordinaten sind Pixel [x, y, Breite, Höhe] im Ausgangsbild {WIDTH} × {HEIGHT}. "
               "Die verkleinerte Anzeige ändert die Koordinaten nicht.")


def crop_width(xywh: list[int], max_width: int = 480, max_height: int = 420) -> int:
    """Anzeigebreite so, dass auch hohe Regionen nicht übermäßig viel Platz einnehmen."""
    w, h = xywh[2], xywh[3]
    return max(1, min(w, max_width, round(max_height * w / h)))


def region_editor(region: dict) -> list[int]:
    """Bearbeitung einer Region; liefert die für die Vorschau gültigen Koordinaten."""
    region_id = region["id"]
    st.markdown(f"**{region['label_de']}** · `{region_id}`")
    ui.status_badge(region["review_status"])
    cols = st.columns(4)
    for col, key, label, limit, saved in zip(cols, "xywh", ["x", "y", "Breite", "Höhe"],
                                             [WIDTH, HEIGHT, WIDTH, HEIGHT], region["xywh"]):
        col.number_input(label, min_value=0, max_value=limit, value=saved, step=1, key=f"{region_id}-{key}")
    xywh = input_xywh(region_id)
    problems = regions.bounds_problems(xywh, WIDTH, HEIGHT)
    for problem in problems:
        st.error(problem)
    unsaved = xywh != region["xywh"]
    ui.unsaved_note(unsaved, f"Gespeichert ist {region['xywh']}. "
                             "Speichern setzt den Prüfstand dieser Region auf „Entwurf“ zurück.")
    shown = region["xywh"] if problems else xywh
    st.image(regions.crop(page_image(), shown), width=crop_width(shown),
             caption="Ausschnitt mit den eingegebenen Werten" if unsaved else "Ausschnitt (gespeicherter Stand)")
    buttons = st.columns(2)
    buttons[0].button("Koordinaten speichern", key=f"{region_id}-save", on_click=save_coordinates,
                      args=(region_id,), disabled=not unsaved or bool(problems))
    buttons[1].button("Eingaben verwerfen", key=f"{region_id}-discard", on_click=discard_coordinates,
                      args=(region_id, region["xywh"]), disabled=not unsaved)

    st.divider()
    if region["review_status"] == review.REGION_REVIEWED:
        ui.confirmed_note(record, region_id)
    else:
        ui.confirm_controls(
            f"{region_id}-review",
            "Die gespeicherten Grenzen umfassen den Bereich vollständig und knapp. "
            "Keine Aussage über Bildinhalt oder Transkription.",
            "Ich habe die gespeicherten Grenzen dieser Region am Bild geprüft.",
            confirm_region, (region_id, region["xywh"]),
            blocked_de="Erst die Eingaben speichern oder verwerfen." if unsaved else None)
    return shown


def description_tab() -> None:
    description = record["image_description"]
    st.markdown("**Erste Beobachtung** (unverändert)")
    ui.source_text(description["observation_de"])
    st.text_area("Arbeitsbeschreibung", value=description["working_description_de"], key="description")
    ui.unsaved_note(st.session_state["description"].strip() != description["working_description_de"])
    st.button("Beschreibung speichern", key="description-save", on_click=save_description)

    for region in record["region_annotations"]:
        if "keywords_de" in region:
            st.divider()
            keyword_editor(region)


def keyword_editor(region: dict) -> None:
    region_id = region["id"]
    st.markdown(f"**Suchbegriffe für „{region['label_de']}“** · `{region_id}`")
    st.caption("Projektlokale Begriffe, keine geprüften GND-Verknüpfungen.")
    ui.status_badge(region["keyword_review_status"])
    st.text_area("Ein Begriff pro Zeile", value="\n".join(region["keywords_de"]), key=f"{region_id}-keywords")
    unsaved = keyword_input(region_id) != region["keywords_de"]
    ui.unsaved_note(unsaved, "Speichern setzt die Bestätigung der Suchbegriffe zurück.")
    st.button("Suchbegriffe speichern", key=f"{region_id}-keywords-save", on_click=save_keywords,
              args=(region_id,))
    if region["keyword_review_status"] == review.KEYWORDS_ACCEPTED:
        ui.confirmed_note(record, f"{region_id}/keywords_de")
    else:
        ui.confirm_controls(
            f"{region_id}-keywords-review",
            "Die gespeicherten Begriffe beschreiben den Bildinhalt zutreffend.",
            "Ich habe die Suchbegriffe am Bild geprüft.",
            confirm_keywords, (region_id, region["keywords_de"]),
            blocked_de="Erst die Eingaben speichern." if unsaved else None)


def transcription_tab() -> None:
    transcription = record["transcription"]
    ocr = record["ocr_result"]
    st.badge("Keine Ground Truth", icon=":material/block:", color="gray")
    st.caption(f"{transcription['review_note_de']} Bildtitel und Verlagsangabe werden einzeln geprüft.")

    for region in record["region_annotations"]:
        if region.get("transcription_field"):
            with st.container(border=True):
                transcription_editor(region, ocr if ocr["region_id"] == region["id"] else None)

    with st.expander("Erste Lesung (unverändert, mit Zeilenumbruch)"):
        st.code(transcription["initial_user_transcription"], language=None)


def transcription_editor(region: dict, ocr: dict | None) -> None:
    transcription = record["transcription"]
    field = region["transcription_field"]
    status = transcription["review_status_by_field"][field]
    st.markdown(f"**{region['label_de']}** · `{region['id']}`")
    ui.status_badge(status)
    st.image(regions.crop(page_image(), region["xywh"]), width=min(region["xywh"][2], 730))
    if ocr:
        ocr_block(ocr)
    st.text_input(f"Transkription: {region['label_de']}", value=transcription[field], key=field)
    unsaved = st.session_state[field] != transcription[field]
    ui.unsaved_note(unsaved, "Speichern setzt nur den Prüfstand dieses Textes auf „vorläufig“.")
    st.button("Speichern", key=f"{field}-save", on_click=save_transcription, args=(field,))
    if status == review.TRANSCRIPTION_REVIEWED:
        ui.confirmed_note(record, f"transcription/{field}")
    else:
        ui.confirm_controls(
            f"{field}-review",
            f"Die gespeicherte Lesung „{region['label_de']}“ stimmt mit der Vorlage überein. "
            "Das ist keine Freigabe als Ground Truth.",
            "Ich habe diesen Text an der Vorlage geprüft.",
            confirm_transcription, (field, transcription[field]),
            blocked_de="Erst die Eingabe speichern." if unsaved else None)


def ocr_block(ocr: dict) -> None:
    meta = store.read_json(store.SOURCE_DIR / ocr["result_file"])
    st.markdown("Gespeicherte OCR-Ausgabe (unverändert, ungeprüft)")
    st.code(ocr["raw_text"], language=None)
    with st.expander("Technische Angaben zum OCR-Lauf"):
        st.text(f"Genaue Zeichenfolge: {ocr['raw_text']!r} ({len(ocr['raw_text'])} Zeichen)\n"
                f"{meta['engine_version']}, Modell {meta['language_model']}, Revision {meta['model_revision']}\n"
                f"OEM {meta['engine_mode']}, PSM {meta['page_segmentation_mode']}, "
                f"Vorverarbeitung: {meta['preprocessing']}\n"
                f"Eingabebild: {meta['input_file']} (SHA-256 {meta['input_sha256'][:16]}…)")


def validation_tab() -> None:
    findings = validate.run_all(working)
    show = {validate.TECHNICAL: st.error, validate.REVIEW: st.warning, validate.NOT_RUN: st.info}
    for category, label in validate.CATEGORY_LABELS_DE.items():
        selected = [f for f in findings if f.category == category]
        st.markdown(f"#### {label}: {len(selected)}")
        for finding in selected:
            show[category](f"{finding.message_de}  \nCode: {finding.code}")
        if not selected:
            st.success("Keine.", icon=":material/check:")
    st.markdown("#### Bewusst leere optionale Angaben")
    st.write((", ".join(validate.unknown_optional_fields(record)) or "Keine.") + " (kein Fehler)")


def export_tab() -> None:
    st.write("Der JSON-Export enthält den vollständigen Arbeitsstand samt Herkunft, Rechten und Prüfprotokoll. "
             "Die CSV-Datei enthält eine Zeile je Region mit Herkunfts- und Lizenzangaben.")
    state, later, exported = export_state()
    st.button("JSON und CSV exportieren", key="export", on_click=run_export, type="primary")
    if state == "none":
        st.info("Noch kein Export vorhanden.")
    elif state == "foreign":
        st.error("Der vorhandene Export stammt nicht aus diesem Arbeitsstand (Änderungsprotokoll passt nicht). "
                 "Bitte neu exportieren.")
    elif state == "stale":
        changes = "\n".join(f"- {c['area_de']} ({ui.local_time(c['saved_at'])})" for c in later)
        st.warning(f"Export veraltet: erstellt {ui.local_time(exported['exported_at'])}. Danach gespeichert:\n"
                   f"{changes}\n\nDas sind spätere Bearbeitungen, keine Exportfehler. "
                   "Für die Rückladeprüfung bitte neu exportieren.")
    else:
        st.success(f"Export aktuell: erstellt {ui.local_time(exported['exported_at'])}, "
                   "seitdem nichts gespeichert.")

    if state != "none":
        st.button("Export erneut laden und prüfen", key="roundtrip", on_click=run_roundtrip,
                  disabled=state != "current")
        if state != "current":
            st.caption("Gesperrt: Die Rückladeprüfung ist nur für einen aktuellen Export aussagekräftig.")
        result = st.session_state.get("roundtrip_result")
        if state == "current" and result and result[0] == exported["exported_at"]:
            for label, ok in result[1]:
                if ok:
                    st.success(f"Erhalten: {label}", icon=":material/check:")
                else:
                    st.error(f"Abweichung: {label}", icon=":material/error:")
            if result[2]:
                st.markdown("Abweichende Felder im Export:\n" + "\n".join(f"- `{p}`" for p in result[2]))
    if CSV_EXPORT.exists():
        with st.expander(f"Inhalt von exports/{CSV_EXPORT.name} (Stand des Exports)"):
            with CSV_EXPORT.open(encoding="utf-8-sig", newline="") as handle:
                st.dataframe(list(csv.DictReader(handle)), hide_index=True)

    st.markdown("#### Prüfprotokoll")
    log = record.get("review_log", [])
    if not log:
        st.info("Noch keine Änderungen oder Bestätigungen protokolliert.")
    else:
        st.dataframe([{"Zeitpunkt": ui.local_time(e["at"]), "Bereich": e["area"], "Vorgang": e["action"],
                       "Person": e.get("by", "")} for e in log], hide_index=True)


sidebar()
st.title("Kinderbuch-Bildlabor")
st.caption("Pilotobjekt mit offenen Prüfständen. Ein Demoobjekt, kein geprüfter Bestand.")
if notice := st.session_state.pop("notice", None):
    st.error(notice, icon=":material/error:")
tabs = st.tabs(["Übersicht", "Bibliotheksdaten", "Regionen", "Beschreibung", "Transkription", "Prüfung", "Export"])
views = [overview_tab, lambda: library_view.render(record), region_tab, description_tab, transcription_tab,
         validation_tab, export_tab]
for tab, view in zip(tabs, views):
    with tab:
        view()
