import hashlib

import pytest

from kinderbuch_bildlabor import colibri

CSV = (
    "ppn,groundtruth,classification,note\n"
    "a,Abbildung,Karte,x\n"
    "b,Abbildung,Karte,y\n"
    "c,-0,Karte,z\n"
    "d,,Karte,z\n"
    'e,Abbildung,Druckermarke,"eins, zwei\nDrei"\n'
    "f,Ölgemälde,Abbildung,ü\n"
    'g,"Abbildung,Initiale",Karte,q\n'
)


def write(tmp_path, text=CSV):
    path = tmp_path / "c.csv"
    path.write_bytes(text.encode())
    return path


def test_counts(tmp_path):
    path = write(tmp_path)
    before = path.read_bytes()
    result = colibri.aggregate(path)
    assert result.cells == {
        ("Abbildung", "Karte"): 2,
        ("Abbildung", "Druckermarke"): 1,
        ("Ölgemälde", "Abbildung"): 1,
        ("Abbildung,Initiale", "Karte"): 1,
    }
    assert (result.rows, result.without_manual) == (7, 2)
    assert result.sha256 == hashlib.sha256(before).hexdigest()
    assert path.read_bytes() == before


def test_header_only(tmp_path):
    result = colibri.aggregate(write(tmp_path, "groundtruth,classification\n"))
    assert (result.cells, result.rows, result.without_manual) == ({}, 0, 0)


def test_missing_column(tmp_path):
    with pytest.raises(ValueError, match="classification"):
        colibri.aggregate(write(tmp_path, "groundtruth,x\na,b\n"))


SAMPLE_CSV = "file,groundtruth,classification\n" + "".join(
    f"data/PPN1/{i:08d}_0.jpg,{m},{a}\n"
    for i, (m, a) in enumerate(
        [("Abbildung", "Karte")] * 20
        + [("Abbildung", "Abbildung")] * 5
        + [("-0", "Karte")] * 5
        + [("Karte", "Exlibris")] * 2
    )
)


def test_sample_reproducible_and_stratified(tmp_path):
    from kinderbuch_bildlabor import colibri_sample

    path = write(tmp_path, SAMPLE_CSV)
    first = colibri_sample.sample_disagreements(path, per_pair=3)
    assert first == colibri_sample.sample_disagreements(path, per_pair=3)
    pairs = [(r["groundtruth"], r["classification"]) for r in first]
    assert pairs.count(("Abbildung", "Karte")) == 3
    assert pairs.count(("Karte", "Exlibris")) == 2
    assert all(p[0] not in ("-0", "") and p[0] != p[1] for p in pairs)
    assert colibri_sample.scan_url(first[0]).startswith("https://content.")
