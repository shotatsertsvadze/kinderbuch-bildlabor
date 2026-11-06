"""Auswertung der gespeicherten OAI-PMH-Antwort: OAI-Hülle, METS und eingebettetes MODS.

Das Buch wird über die Wurzel der logischen METS-Struktur gefunden, nicht über eine feste ID.
Jedes Textelement des Buch-MODS wird mit seinem exakten XPath erfasst; nur ausgewählte Elemente
erhalten ein lokales Zielfeld. So geht keine wiederholte oder unzugeordnete Angabe verloren.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "mets": "http://www.loc.gov/METS/",
    "mods": "http://www.loc.gov/mods/v3",
    "xlink": "http://www.w3.org/1999/xlink",
    "zvdd": "http://zvdd.gdz-cms.de/",
}
PREFIX = {uri: prefix for prefix, uri in NS.items()}
METS_PATH = "oai:GetRecord/oai:record/oai:metadata/mets:mets"

# (XPath-Regel relativ zum Buch-MODS, lokales Zielfeld oder None, Hinweis)
RULES = [
    ("mods:titleInfo/mods:title", "title", "Haupttitel"),
    ("mods:titleInfo/mods:subTitle", None, "Untertitel; lokal kein Feld"),
    (
        "mods:originInfo[@eventType='publication']/mods:place/mods:placeTerm",
        "publication_place",
        "Erscheinungsort (Ereignis: Veröffentlichung)",
    ),
    (
        "mods:originInfo[@eventType='publication']/mods:publisher",
        "publisher",
        "Verlag (Ereignis: Veröffentlichung)",
    ),
    (
        "mods:originInfo[@eventType='publication']/mods:dateIssued",
        "publication_date",
        "Erscheinungsjahr",
    ),
    (
        "mods:originInfo[@eventType='digitization']/mods:place/mods:placeTerm",
        None,
        "Ort der Digitalisierung",
    ),
    (
        "mods:originInfo[@eventType='digitization']/mods:publisher",
        None,
        "Digitalisierende Einrichtung, nicht der Verlag des Buches",
    ),
    (
        "mods:originInfo[@eventType='digitization']/mods:dateCaptured",
        None,
        "Jahr der Digitalisierung",
    ),
    (
        "mods:originInfo[@eventType='digitization']/mods:edition",
        None,
        "Ausgabe der Digitalisierung",
    ),
    (
        "mods:language/mods:languageTerm",
        None,
        "Sprache (ISO 639-2/B); lokal noch kein Feld",
    ),
    (
        "mods:language/mods:scriptTerm",
        None,
        "Schrift (ISO 15924, numerisch; 217 = Latf, Fraktur)",
    ),
    (
        "mods:recordInfo/mods:recordIdentifier",
        "source.ppn",
        "Kennung des Digitalisats im GBV",
    ),
    ("mods:identifier", None, "Persistente Adresse des Digitalisats"),
    (
        "mods:relatedItem[@type='original']/mods:recordInfo/mods:recordIdentifier",
        None,
        "Kennung der gedruckten Vorlage",
    ),
    (
        "mods:relatedItem[@type='series']/mods:titleInfo/mods:title",
        None,
        "Reihe beziehungsweise Sammlung",
    ),
    ("mods:location/mods:physicalLocation", None, "Besitzende Einrichtung"),
    ("mods:location/mods:shelfLocator", None, "Signatur"),
    (
        "mods:physicalDescription/mods:extent",
        None,
        "Umfang und Format; wiederholtes Feld",
    ),
    (
        "mods:accessCondition[@type='use and reproduction']",
        "rights_statement",
        "Rechte am Quellwerk",
    ),
    ("mods:accessCondition[@type='restriction on access']", None, "Zugangsstatus"),
    ("mods:name/mods:namePart", None, "Namensbestandteil"),
    ("mods:name/mods:nameIdentifier", None, "Personenkennung"),
    ("mods:name/mods:role/mods:roleTerm", None, "Rolle (MARC-Relator-Code)"),
    ("mods:classification", None, "Sammlungsklassifikation"),
    ("mods:genre", None, "Gattung"),
    ("mods:typeOfResource", None, "Ressourcentyp"),
    ("mods:physicalDescription/mods:digitalOrigin", None, "Herkunft des Digitalisats"),
]
RELATOR_DE = {"aut": "Verfasser", "fnd": "Geldgeber", "ill": "Illustrator"}


@dataclass(frozen=True)
class SourceValue:
    path: str
    value: str
    attributes: str
    target: str | None
    note_de: str


def parse(path) -> ET.Element:
    return ET.parse(path).getroot()


class MissingMetadata(ValueError):
    pass


def mets(root: ET.Element) -> ET.Element:
    document = root.find(METS_PATH, NS)
    if document is None:
        raise MissingMetadata("METS-Dokument fehlt in der OAI-Hülle.")
    return document


def envelope(root: ET.Element) -> dict[str, str | None]:
    header = root.find("oai:GetRecord/oai:record/oai:header", NS)
    request = root.find("oai:request", NS)
    assert header is not None and request is not None
    return {
        "identifier": header.findtext("oai:identifier", namespaces=NS),
        "datestamp": header.findtext("oai:datestamp", namespaces=NS),
        "set_spec": header.findtext("oai:setSpec", namespaces=NS),
        "response_date": root.findtext("oai:responseDate", namespaces=NS),
        "verb": request.get("verb"),
        "metadata_prefix": request.get("metadataPrefix"),
    }


def book_mods_path(dmd_id: str) -> str:
    return f"{METS_PATH}/mets:dmdSec[@ID='{dmd_id}']/mets:mdWrap/mets:xmlData/mods:mods"


def book_mods(root: ET.Element) -> tuple[str, ET.Element]:
    """Buch-MODS über die DMDID an der Wurzel der logischen Struktur (TYPE monograph)."""
    top = mets(root).find("mets:structMap[@TYPE='LOGICAL']/mets:div", NS)
    if top is None:
        raise MissingMetadata("Logische METS-Wurzel fehlt.")
    dmd_id = top.get("DMDID")
    if not dmd_id:
        raise MissingMetadata("DMDID der logischen METS-Wurzel fehlt.")
    mods = root.find(book_mods_path(dmd_id), NS)
    if mods is None:
        raise MissingMetadata(f"Buch-MODS für DMDID {dmd_id} fehlt.")
    return dmd_id, mods


TYPE_DE = {
    "illustration": "Illustration",
    "chapter": "Kapitel",
    "section": "Abschnitt",
    "monograph": "Buch",
}


def structure_for_page(root: ET.Element, phys_id: str) -> dict | None:
    """Engstes logisches Strukturelement unterhalb des Buches, das per smLink auf diese Seite zeigt."""
    document = mets(root)
    xlink = "{" + NS["xlink"] + "}"
    linked = {
        link.get(xlink + "from")
        for link in document.iter("{" + NS["mets"] + "}smLink")
        if link.get(xlink + "to") == phys_id
    }
    top = document.find("mets:structMap[@TYPE='LOGICAL']/mets:div", NS)
    assert top is not None
    # Dokumentreihenfolge: das zuletzt gefundene Element ist das am tiefsten verschachtelte
    found = [
        div
        for div in top.iter("{" + NS["mets"] + "}div")
        if div is not top and div.get("ID") in linked
    ]
    if not found:
        return None
    div = found[-1]
    dmd_id = div.get("DMDID")
    title = (
        document.findtext(f"mets:dmdSec[@ID='{dmd_id}']//mods:title", namespaces=NS)
        if dmd_id
        else None
    )
    return {
        "log_id": div.get("ID"),
        "type": div.get("TYPE"),
        "type_de": TYPE_DE.get(div.get("TYPE", ""), div.get("TYPE", "")),
        "dmd_id": dmd_id,
        "label": div.get("LABEL"),
        "title": title,
    }


def page_label(root: ET.Element, phys_id: str) -> str | None:
    div = mets(root).find(
        f"mets:structMap[@TYPE='PHYSICAL']//mets:div[@ID='{phys_id}']", NS
    )
    assert div is not None
    return div.get("ORDERLABEL")


def qualified(name: str) -> str:
    uri, _, local = name[1:].partition("}") if name.startswith("{") else ("", "", name)
    return f"{PREFIX[uri]}:{local}" if uri else local


def relative_path(base: ET.Element, element: ET.Element, parents: dict) -> str:
    """Exakter XPath mit Positionsangabe, falls ein Element mehrfach vorkommt."""
    steps = []
    while element is not base:
        parent = parents[element]
        same = [child for child in parent if child.tag == element.tag]
        step = qualified(element.tag)
        steps.append(f"{step}[{same.index(element) + 1}]" if len(same) > 1 else step)
        element = parent
    return "./" + "/".join(reversed(steps))


def attribute_text(element: ET.Element) -> str:
    return "; ".join(f"{qualified(k)}={v}" for k, v in element.attrib.items())


def persons(mods: ET.Element) -> list[dict]:
    """Personen und Körperschaften mit Rollen; Zielfeld nur bei Rolle 'aut'."""
    result = []
    for name in mods.findall("mods:name", NS):
        roles = [term.text for term in name.findall("mods:role/mods:roleTerm", NS)]
        shown = name.find("mods:displayForm", NS)
        if shown is None:
            shown = name.find("mods:namePart", NS)
        assert shown is not None
        result.append(
            {
                "element": shown,
                "display": shown.text,
                "type": name.get("type"),
                "roles": roles,
                "roles_de": ", ".join(
                    f"{r} = {RELATOR_DE.get(r or '', 'unbekannte Rolle')}"
                    for r in roles
                ),
                "authority_uri": name.get("valueURI"),
                "identifiers": [
                    f"{e.get('type')}: {e.text}"
                    for e in name.findall("mods:nameIdentifier", NS)
                ],
                "name_attributes": attribute_text(name),
                "target": "author_display" if "aut" in roles else None,
            }
        )
    return result


def mapping_rows(mods: ET.Element) -> list[SourceValue]:
    """Alle Textelemente des Buch-MODS in Dokumentreihenfolge, mit Zielfeld laut Regel."""
    parents = {child: parent for parent in mods.iter() for child in parent}
    assigned = {}
    for rule, target, note in RULES:
        for element in mods.findall(rule, NS):
            assigned[element] = (target, note, "")
    for person in persons(mods):
        note = f"Name ({person['type']}), Rolle: {person['roles_de']}"
        if not person["target"]:
            note += "; nicht als Verfasser zugeordnet"
        # Attribute des name-Elements (z. B. GND-URI) gehören zur Namenszeile
        assigned[person["element"]] = (
            person["target"],
            note,
            f"name: {person['name_attributes']}",
        )
    rows = []
    for element in mods.iter():
        text = (element.text or "").strip()
        if not text or len(element):
            continue
        target, note, extra = assigned.get(element, (None, "noch nicht zugeordnet", ""))
        attributes = "; ".join(
            part for part in (attribute_text(element), extra) if part
        )
        rows.append(
            SourceValue(
                relative_path(mods, element, parents), text, attributes, target, note
            )
        )
    return rows


COMPARED = [
    ("title", "Titel"),
    ("author_display", "Verfasser"),
    ("publication_place", "Erscheinungsort"),
    ("publisher", "Verlag"),
    ("publication_date", "Erscheinungsjahr"),
    ("rights_statement", "Rechte"),
]


MATCH, BOTH_EMPTY = "übereinstimmend", "in beiden nicht angegeben"
CONSISTENT = {MATCH, BOTH_EMPTY}


def outcome(local: str | None, source_values: list[str]) -> str:
    if not source_values:
        return BOTH_EMPTY if local is None else "fehlt im MODS"
    if len(source_values) > 1:
        return "mehrdeutig"
    return MATCH if source_values[0] == local else "abweichend"


def compare(record: dict, rows: list[SourceValue]) -> list[dict]:
    """Exakter Zeichenvergleich ohne Normalisierung; nichts wird übernommen."""
    biblio = record["bibliographic_metadata_from_colibri"]
    fields = [(key, label, biblio.get(key), "Colibri") for key, label in COMPARED]
    fields.append(("source.ppn", "PPN", record["source"]["ppn"], "Pilotdatensatz"))
    result = []
    for key, label, local, origin in fields:
        values = list(dict.fromkeys(r.value for r in rows if r.target == key))
        result.append(
            {
                "field": key,
                "label_de": label,
                "local": local,
                "local_origin": origin,
                "source": values,
                "outcome": outcome(local, values),
            }
        )
    return result


def content_checks(root: ET.Element, record: dict) -> list[tuple[str, bool]]:
    source = record["source"]
    info = envelope(root)
    try:
        dmd_id, mods = book_mods(root)
    except MissingMetadata as error:
        return [(str(error), False)]
    structure = structure_for_page(root, source["physical_page_id"])
    record_id = mods.findtext("mods:recordInfo/mods:recordIdentifier", namespaces=NS)
    checks = [
        (
            "OAI-Antwort ist GetRecord im Format mets",
            info["verb"] == "GetRecord" and info["metadata_prefix"] == "mets",
        ),
        (
            f"OAI-Kennung bezieht sich auf {source['ppn']}",
            (info["identifier"] or "").endswith(":" + source["ppn"]),
        ),
        ("METS-Dokument in der OAI-Hülle vorhanden", True),
        (f"Buch-MODS über die logische Struktur gefunden ({dmd_id})", True),
        (
            f"MODS-Datensatzkennung entspricht {source['ppn']}",
            record_id == source["ppn"],
        ),
        (
            f"Seite {source['physical_page_id']} ist mit einem logischen Strukturelement verknüpft",
            structure is not None,
        ),
    ]
    if "DMDID=" in source["viewer_url"]:
        checks.append(
            (
                "DMDID des verknüpften Strukturelements steht in der Viewer-URL",
                structure is not None
                and f"DMDID={structure['dmd_id']}" in source["viewer_url"],
            )
        )
    return checks
