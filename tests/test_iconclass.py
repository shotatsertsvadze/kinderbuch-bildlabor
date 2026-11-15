from kinderbuch_bildlabor import iconclass


def test_suggest_matches_german_words_in_file_order():
    found = iconclass.suggest("Ein Hund im Wald, daneben ein Baum")
    assert [s.notation for s in found] == ["25F2", "25G", "25H"]
    assert found[2].line == "Iconclass 25H Landschaften"


def test_suggest_without_match_is_empty():
    assert iconclass.suggest("Vier Personen") == []
    assert iconclass.suggest("") == []


def test_every_entry_has_notation_label_and_words():
    for entry in iconclass.entries():
        assert entry["notation"] and entry["label_de"] and entry["woerter"]
