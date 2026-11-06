import copy
import xml.etree.ElementTree as ET

import pytest

from kinderbuch_bildlabor import oai, store

XML_TEXT = store.OAI_RECORD.read_text(encoding="utf-8")


def real():
    return oai.parse(store.OAI_RECORD)


def variant(tmp_path, old: str, new: str):
    """Variante der echten Antwort mit genau einer Textersetzung."""
    assert XML_TEXT.count(old) == 1
    path = tmp_path / "variant.xml"
    path.write_text(XML_TEXT.replace(old, new), encoding="utf-8")
    return oai.parse(path)


def rows_of(root):
    return oai.mapping_rows(oai.book_mods(root)[1])


def by_path(rows):
    return {r.path: r for r in rows}


def pilot_record():
    return store.new_working_copy()["record"]


def test_oai_envelope_mets_and_mods_are_distinguished():
    root = real()
    assert root.tag == "{http://www.openarchives.org/OAI/2.0/}OAI-PMH"
    assert oai.envelope(root) == {
        "identifier": "oai:digital.staatsbibliothek-berlin.de:PPN1814684999",
        "datestamp": "2025-04-24T13:41:27Z", "set_spec": "kinder.und.jugendbuecher",
        "response_date": "2026-11-06T14:08:39Z", "verb": "GetRecord", "metadata_prefix": "mets"}
    assert oai.mets(root).tag == "{http://www.loc.gov/METS/}mets"
    assert len(oai.mets(root).findall("mets:dmdSec", oai.NS)) == 4


def test_book_is_found_via_logical_structure_and_illustration_via_page_link():
    root = real()
    dmd_id, mods = oai.book_mods(root)
    assert dmd_id == "DMDLOG_0000"
    assert mods.findtext("mods:titleInfo/mods:title", namespaces=oai.NS) == "Die Heimath in Amerika"
    assert oai.illustration_for_page(root, "PHYS_0006") == {
        "log_id": "LOG_0002", "dmd_id": "DMDLOG_0001",
        "label": "Die Heimath in Amerika.", "title": "Die Heimath in Amerika."}
    assert oai.page_label(root, "PHYS_0006") == " - "


def test_every_text_element_is_kept_and_its_xpath_leads_back_to_the_value():
    root = real()
    dmd_id, mods = oai.book_mods(root)
    rows = oai.mapping_rows(mods)
    leaves = [e for e in mods.iter() if (e.text or "").strip() and not len(e)]
    assert len(rows) == len(leaves) == 37
    for row in rows:
        assert root.find(oai.book_mods_path(dmd_id) + row.path[1:], oai.NS).text.strip() == row.value


def test_repeated_and_context_dependent_values_are_kept():
    rows = by_path(rows_of(real()))
    assert [rows[f"./mods:physicalDescription/mods:extent[{i}]"].value for i in (1, 2, 3)] == [
        "86 Seiten", "8°", "Frontispiz"]
    publication = rows["./mods:originInfo[1]/mods:publisher"]
    digitization = rows["./mods:originInfo[2]/mods:publisher"]
    assert (publication.value, publication.target) == ("J. A. Schlosser's Buch- und Kunsthandlung", "publisher")
    assert digitization.value.startswith("Staatsbibliothek zu Berlin") and digitization.target is None
    assert rows["./mods:accessCondition[1]"].target == "rights_statement"
    assert rows["./mods:accessCondition[2]"].value == "open access"


def test_persons_keep_roles_and_authority_links():
    people = oai.persons(oai.book_mods(real())[1])
    assert [(p["display"], p["roles"], p["target"]) for p in people] == [
        ("Schmid, Christoph, von", ["aut"], "author_display"),
        ("Deutsche Forschungsgemeinschaft", ["fnd"], None)]
    assert people[0]["authority_uri"] == "http://d-nb.info/gnd/118759523"
    assert people[0]["identifiers"] == ["gbv-ppn: 133431010"]


def test_language_and_identifiers_are_extracted_with_their_attributes():
    rows = by_path(rows_of(real()))
    assert (rows["./mods:language/mods:languageTerm"].value,
            rows["./mods:language/mods:languageTerm"].attributes) == ("ger", "authority=iso639-2b; type=code")
    assert rows["./mods:language/mods:scriptTerm"].value == "217"
    assert rows["./mods:recordInfo/mods:recordIdentifier"].value == "PPN1814684999"
    assert rows["./mods:identifier"].attributes == "type=purl"
    assert rows["./mods:relatedItem[1]/mods:recordInfo/mods:recordIdentifier"].value == "PPN59957240X"


def test_comparison_with_pilot_record_matches_and_does_not_change_it():
    record = pilot_record()
    before = copy.deepcopy(record)
    result = oai.compare(record, rows_of(real()))
    assert [(c["label_de"], c["outcome"]) for c in result] == [
        ("Titel", "übereinstimmend"), ("Verfasser", "übereinstimmend"), ("Erscheinungsort", "übereinstimmend"),
        ("Verlag", "übereinstimmend"), ("Erscheinungsjahr", "übereinstimmend"), ("Rechte", "übereinstimmend"),
        ("PPN", "übereinstimmend")]
    assert record == before


def test_comparison_reports_difference_without_normalising():
    record = pilot_record()
    record["bibliographic_metadata_from_colibri"]["publisher"] = "J. A. Schlosser’s Buch- und Kunsthandlung"
    result = {c["field"]: c for c in oai.compare(record, rows_of(real()))}
    assert result["publisher"]["outcome"] == "abweichend"
    assert result["publisher"]["source"] == ["J. A. Schlosser's Buch- und Kunsthandlung"]


def test_repeated_title_is_reported_as_ambiguous(tmp_path):
    root = variant(tmp_path, "<mods:title>Die Heimath in Amerika</mods:title>",
                   "<mods:title>Die Heimath in Amerika</mods:title><mods:title>Die Heimat in Amerika</mods:title>")
    result = {c["field"]: c for c in oai.compare(pilot_record(), rows_of(root))}
    assert result["title"]["outcome"] == "mehrdeutig"
    assert result["title"]["source"] == ["Die Heimath in Amerika", "Die Heimat in Amerika"]


def test_missing_source_value_is_reported(tmp_path):
    root = variant(tmp_path, '<mods:dateIssued encoding="iso8601" keyDate="yes">1850</mods:dateIssued>', "")
    result = {c["field"]: c for c in oai.compare(pilot_record(), rows_of(root))}
    assert result["publication_date"]["outcome"] == "fehlt im MODS"


def test_content_checks_pass_for_real_file_and_fail_for_other_ppn():
    assert all(ok for _, ok in oai.content_checks(real(), pilot_record()))
    other = pilot_record()
    other["source"]["ppn"] = "PPN000000000"
    failed = [label for label, ok in oai.content_checks(real(), other) if not ok]
    assert failed == ["OAI-Kennung bezieht sich auf PPN000000000", "MODS-Datensatzkennung entspricht PPN000000000"]


def test_malformed_xml_raises_parse_error(tmp_path):
    path = tmp_path / "broken.xml"
    path.write_text(XML_TEXT[:5000], encoding="utf-8")
    with pytest.raises(ET.ParseError):
        oai.parse(path)


def test_source_xml_stays_unchanged():
    manifest = {f["file"]: f["sha256"] for f in store.read_json(store.MANIFEST)["files"]}
    rows_of(real())
    assert store.sha256(store.OAI_RECORD) == manifest["pilot_001_oai_mets.xml"]
