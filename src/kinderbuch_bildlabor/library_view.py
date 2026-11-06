"""Reiter „Bibliotheksdaten“: gespeicherte OAI-PMH-Antwort, MODS-Mapping und Vergleich."""

import xml.etree.ElementTree as ET

import streamlit as st

from kinderbuch_bildlabor import oai, store


@st.cache_resource
def parsed_source() -> ET.Element:
    """Die Quelldatei ist unveränderlich; einmal geparst genügt."""
    return oai.parse(store.OAI_RECORD)


def target_label(target: str | None) -> str:
    if target is None:
        return "–"
    return target if target.startswith("source.") else f"bibliographic_metadata_from_colibri.{target}"


def render(record: dict) -> None:
    st.caption(f"Gespeicherte OAI-PMH-Antwort aus {store.OAI_RECORD.name}. Kein Live-Abruf. "
               "Es wird nichts automatisch in den lokalen Datensatz übernommen.")
    try:
        root = parsed_source()
    except ET.ParseError as error:
        st.error(f"XML-Parsing fehlgeschlagen: {error}", icon=":material/error:")
        return

    checks = oai.content_checks(root, record)
    passed = sum(ok for _, ok in checks)
    cols = st.columns(3)
    with cols[0]:
        st.success("XML-Parsing: erfolgreich", icon=":material/check:")
    with cols[1]:
        (st.success if passed == len(checks) else st.warning)(
            f"Inhaltliche Prüfungen: {passed} von {len(checks)} bestanden",
            icon=":material/check:" if passed == len(checks) else ":material/warning:")
    with cols[2]:
        st.info("XSD-Validierung: nicht ausgeführt", icon=":material/pending:")

    dmd_id, mods = oai.book_mods(root)
    rows = oai.mapping_rows(mods)
    structure(root, dmd_id, len(rows))
    comparison(record, rows)
    pilot_link(root, record)
    people(mods)
    mapping(rows, dmd_id)
    technical(root, checks, dmd_id)


def structure(root: ET.Element, dmd_id: str, row_count: int) -> None:
    info = oai.envelope(root)
    sections = len(oai.mets(root).findall("mets:dmdSec", oai.NS))
    st.markdown("#### Aufbau der Antwort")
    st.markdown(
        f"1. **OAI-PMH-Hülle:** {info['verb']} für `{info['identifier']}`, "
        f"Datumsstempel {info['datestamp']}, Set `{info['set_spec']}`\n"
        f"2. **METS:** {sections} beschreibende Abschnitte (dmdSec); das Buch ist die Wurzel der logischen "
        f"Struktur und verweist auf `{dmd_id}`\n"
        f"3. **MODS (Buch):** {row_count} Textelemente, alle unten aufgeführt")


def comparison(record: dict, rows: list[oai.SourceValue]) -> None:
    st.markdown("#### Vergleich mit den lokalen Buchdaten")
    table = [{"Feld": c["label_de"], "Ergebnis": c["outcome"], "Lokaler Wert": c["local"],
              "Wert im MODS": " | ".join(c["source"]) or "–", "Herkunft lokal": c["local_origin"]}
             for c in oai.compare(record, rows)]
    st.dataframe(table, hide_index=True)
    st.caption("Exakter Zeichenvergleich ohne Normalisierung. Unterschiede werden angezeigt, nicht übernommen.")


def pilot_link(root: ET.Element, record: dict) -> None:
    source = record["source"]
    illustration = oai.illustration_for_page(root, source["physical_page_id"])
    st.markdown("#### Bezug zum Pilotobjekt")
    if illustration is None:
        st.warning(f"Kein Strukturelement „illustration“ ist mit {source['physical_page_id']} verknüpft.")
        return
    label = oai.page_label(root, source["physical_page_id"])
    title = record["transcription"]["working_title"]
    st.markdown(
        f"- Strukturelement `{illustration['log_id']}` (Typ illustration) ist mit `{source['physical_page_id']}` "
        f"verknüpft; Beschreibung in `{illustration['dmd_id']}`\n"
        f"- Titel der Illustration im METS/MODS: „{illustration['title']}“\n"
        f"- Seitenbezeichnung im METS: „{label}“, also keine gedruckte Seitenzahl "
        f"(passt zu „gedruckte Seitenzahl unbekannt“)")
    same = "gleich lautend" if illustration["title"] == title else "abweichend"
    st.caption(f"Die lokale Arbeitstranskription des Bildtitels lautet „{title}“ ({same}). Das ist nur ein Hinweis; "
               "Prüfstände ändern sich dadurch nicht. Die Verlagsangabe auf dem Bildblatt gehört zu einem anderen "
               "Beschreibungskontext und wird nicht mit den Buchdaten verglichen.")


def people(mods: ET.Element) -> None:
    st.markdown("#### Personen und Rollen")
    st.dataframe([{"Name": p["display"], "Typ": p["type"], "Rolle": p["roles_de"],
                   "Normdaten": p["authority_uri"] or "–", "Kennungen": ", ".join(p["identifiers"]) or "–",
                   "Lokales Vergleichsfeld": target_label(p["target"])} for p in oai.persons(mods)], hide_index=True)
    st.caption("Ein Illustrator ist im MODS nicht genannt; das lokale Feld bleibt unbekannt.")


def mapping_table(rows: list[oai.SourceValue]) -> list[dict]:
    return [{"Quellpfad (XPath)": r.path, "Originalwert": r.value,
             "Lokales Vergleichsfeld": target_label(r.target), "Attribute": r.attributes or "–",
             "Hinweis": r.note_de} for r in rows]


def mapping(rows: list[oai.SourceValue], dmd_id: str) -> None:
    st.markdown("#### Mapping: Quellfeld → Originalwert → lokales Feld")
    st.dataframe(mapping_table([r for r in rows if r.target]), hide_index=True)
    st.caption(f"Pfade relativ zum Buch-MODS ({dmd_id}); vollständiger Pfad unter „Technische Details“.")
    with st.expander(f"Alle {len(rows)} Textelemente des Buch-MODS (auch nicht zugeordnete)"):
        st.dataframe(mapping_table(rows), hide_index=True)


def technical(root: ET.Element, checks: list[tuple[str, bool]], dmd_id: str) -> None:
    with st.expander("Technische Details"):
        st.markdown("**Inhaltliche Prüfungen**\n" + "\n".join(
            f"- {'Bestanden' if ok else 'Nicht bestanden'}: {label}" for label, ok in checks))
        st.text(f"Basis-XPath des Buch-MODS:\n/oai:OAI-PMH/{oai.book_mods_path(dmd_id)}\n\n"
                "Namespaces:\n" + "\n".join(f"{prefix} = {uri}" for prefix, uri in oai.NS.items()) +
                f"\n\nSchemaangaben im METS (nicht validiert):\n"
                f"{oai.mets(root).get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation')}\n\n"
                f"Datei: {store.OAI_RECORD.name}, SHA-256 {store.sha256(store.OAI_RECORD)}")
