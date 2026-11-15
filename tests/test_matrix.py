from types import SimpleNamespace

from kinderbuch_bildlabor import matrix


def cur(id, manual, auto):
    source = {"colibri_groundtruth": manual, "colibri_classification": auto}
    return SimpleNamespace(id=id, record={"source": source})


def test_cells_group_by_manual_and_automatic_class():
    table, missing = matrix.cells(
        [
            cur("a", "Abbildung", "Foto"),
            cur("b", "Abbildung", "Foto"),
            cur("c", "X", "X"),
        ]
    )
    assert table == {("Abbildung", "Foto"): ["a", "b"], ("X", "X"): ["c"]}
    assert missing == []


def test_missing_labels_are_counted_separately():
    table, missing = matrix.cells([cur("a", None, "Foto"), cur("b", "X", "")])
    assert table == {}
    assert missing == ["a", "b"]


def test_empty_collection():
    assert matrix.cells([]) == ({}, [])
