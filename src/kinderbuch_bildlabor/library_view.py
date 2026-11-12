"""Reiter „Bibliotheksdaten“: gespeicherte OAI-PMH-Antwort, MODS-Mapping und Vergleich."""

import xml.etree.ElementTree as ET

import streamlit as st

from kinderbuch_bildlabor import oai, store, ui


@st.cache_resource
def parsed_source(path) -> ET.Element:
    """Die Quelldatei ist unveränderlich; einmal geparst genügt."""
    return oai.parse(path)


def target_label(target: str | None) -> str:
    if target is None:
        return "–"
    return (
        target
        if target.startswith("source.")
        else f"bibliographic_metadata_from_colibri.{target}"
    )


def render(record: dict, src: store.ObjectSource) -> None:
    if "oai" not in src.capabilities:
        st.info(
            "OAI/METS-Abgleich nicht ausgeführt: Für diesen Import liegt keine OAI/METS-Quelle vor."
        )
        st.caption("Metadaten stammen aus dem Import, nicht aus Colibri oder MODS.")
        st.json(record["metadata_provenance"])
        return
    st.caption(
        "Ausgewertet wird die gespeicherte OAI-PMH-Antwort zum Buch, ohne Live-Abruf. "
        "Es wird nichts automatisch in den lokalen Datensatz übernommen."
    )
    try:
        root = parsed_source(src.oai_record)
    except ET.ParseError as error:
        st.error(f"XML-Parsing fehlgeschlagen: {error}", icon=ui.ERROR)
        return

    checks = oai.content_checks(root, record)
    passed = sum(ok for _, ok in checks)
    cols = st.columns(3)
    with cols[0]:
        st.success("XML-Parsing: erfolgreich", icon=ui.OK)
    with cols[1]:
        (st.success if passed == len(checks) else st.warning)(
            f"Inhaltliche Prüfungen: {passed} von {len(checks)} bestanden",
            icon=ui.OK if passed == len(checks) else ui.WARNING,
        )
    with cols[2]:
        st.info("XSD-Validierung: nicht ausgeführt", icon=ui.PENDING)

    try:
        dmd_id, mods = oai.book_mods(root)
    except oai.MissingMetadata as error:
        st.error(str(error), icon=ui.ERROR)
        return
    rows = oai.mapping_rows(mods)
    structure(root, dmd_id, len(rows))
    comparison(record, rows)
    page_link(root, record)
    people(mods)
    mapping(rows, dmd_id)
    technical(root, checks, dmd_id, src)


def structure(root: ET.Element, dmd_id: str, row_count: int) -> None:
    info = oai.envelope(root)
    sections = len(oai.mets(root).findall("mets:dmdSec", oai.NS))
    ui.section("Aufbau der Antwort")
    st.markdown(
        f"1. **OAI-PMH-Hülle:** {info['verb']} für `{info['identifier']}`, "
        f"Datumsstempel {info['datestamp']}, Set `{info['set_spec']}`\n"
        f"2. **METS:** {sections} beschreibende Abschnitte (dmdSec); das Buch ist die Wurzel der logischen "
        f"Struktur und verweist auf `{dmd_id}`\n"
        f"3. **MODS (Buch):** {row_count} Textelemente, alle unten aufgeführt"
    )


def comparison(record: dict, rows: list[oai.SourceValue]) -> None:
    ui.section("Vergleich mit den lokalen Buchdaten")
    table = [
        {
            "Feld": c["label_de"],
            "Ergebnis": c["outcome"],
            "Lokaler Wert": c["local"],
            "Wert im MODS": " | ".join(c["source"]) or "–",
            "Herkunft lokal": c["local_origin"],
        }
        for c in oai.compare(record, rows)
    ]
    st.dataframe(table, hide_index=True)
    st.caption(
        "Exakter Zeichenvergleich ohne Normalisierung. Unterschiede werden angezeigt, nicht übernommen."
    )


def page_link(root: ET.Element, record: dict) -> None:
    source = record["source"]
    phys_id = source["physical_page_id"]
    structure = oai.structure_for_page(root, phys_id)
    ui.section("Bezug dieser Seite im METS")
    if structure is None:
        st.warning(
            f"Die Seite {phys_id} ist mit keinem logischen Strukturelement verknüpft."
        )
        return
    label = (oai.page_label(root, phys_id) or "").strip()
    page_text = (
        f"Seitenbezeichnung im METS: „{label}“"
        if label not in ("", "-")
        else "Keine Seitenbezeichnung im METS (passt zu „gedruckte Seitenzahl unbekannt“)"
    )
    st.markdown(
        f"- {phys_id} gehört zum Strukturelement {structure['type_de']} „{structure['title'] or structure['label']}“ "
        f"(`{structure['log_id']}`, Beschreibung in `{structure['dmd_id']}`)\n"
        f"- {page_text}"
    )
    if structure["type"] == "illustration":
        title = record["transcription"]["working_title"]
        same = "gleich lautend" if structure["title"] == title else "abweichend"
        st.caption(
            f"Die Arbeitstranskription des Bildtitels lautet „{title}“ ({same}). Das ist nur ein Hinweis; "
            "Prüfstände ändern sich dadurch nicht. Die Verlagsangabe auf dem Bildblatt gehört zu einem "
            "anderen Beschreibungskontext und wird nicht mit den Buchdaten verglichen."
        )
    else:
        st.caption(
            "Die Illustration ist im METS nicht als eigenes Strukturelement erfasst; die Region in "
            "diesem Projekt ist deshalb die einzige Auszeichnung der Abbildung auf dieser Seite."
        )


def people(mods: ET.Element) -> None:
    ui.section("Personen und Rollen")
    st.dataframe(
        [
            {
                "Name": p["display"],
                "Typ": p["type"],
                "Rolle": p["roles_de"],
                "Normdaten": p["authority_uri"] or "–",
                "Kennungen": ", ".join(p["identifiers"]) or "–",
                "Lokales Vergleichsfeld": target_label(p["target"]),
            }
            for p in oai.persons(mods)
        ],
        hide_index=True,
    )
    st.caption(
        "Ein Illustrator ist im MODS nicht genannt; das lokale Feld bleibt unbekannt."
    )


def mapping_table(rows: list[oai.SourceValue]) -> list[dict]:
    return [
        {
            "Quellpfad (XPath)": r.path,
            "Originalwert": r.value,
            "Lokales Vergleichsfeld": target_label(r.target),
            "Attribute": r.attributes or "–",
            "Hinweis": r.note_de,
        }
        for r in rows
    ]


def mapping(rows: list[oai.SourceValue], dmd_id: str) -> None:
    ui.section("Mapping: Quellfeld → Originalwert → lokales Feld")
    st.dataframe(mapping_table([r for r in rows if r.target]), hide_index=True)
    st.caption(
        f"Pfade relativ zum Buch-MODS ({dmd_id}); vollständiger Pfad unter „Technische Details“."
    )
    with st.expander(
        f"Alle {len(rows)} Textelemente des Buch-MODS (auch nicht zugeordnete)"
    ):
        st.dataframe(mapping_table(rows), hide_index=True)


def technical(
    root: ET.Element,
    checks: list[tuple[str, bool]],
    dmd_id: str,
    src: store.ObjectSource,
) -> None:
    with st.expander("Technische Details"):
        ui.subsection("Inhaltliche Prüfungen")
        st.markdown(
            "\n".join(
                f"- {'Bestanden' if ok else 'Nicht bestanden'}: {label}"
                for label, ok in checks
            )
        )
        st.text(
            f"Basis-XPath des Buch-MODS:\n/oai:OAI-PMH/{oai.book_mods_path(dmd_id)}\n\n"
            "Namespaces:\n"
            + "\n".join(f"{prefix} = {uri}" for prefix, uri in oai.NS.items())
            + f"\n\nSchemaangaben im METS (nicht validiert):\n"
            f"{oai.mets(root).get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation')}\n\n"
            f"Datei: {src.oai_record.relative_to(store.ROOT)}, SHA-256 {store.sha256(src.oai_record)}"
        )
