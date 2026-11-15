from kinderbuch_bildlabor import triage
from kinderbuch_bildlabor.triage import Row


def row(id, disagreement=False, blockers=0, confirmed=0, approved=False):
    return Row(id, id, disagreement, blockers, confirmed, 5, approved)


def test_order_ranks_disagreement_then_blockers_then_fewest_confirmed_approved_last():
    rows = [
        row("done", disagreement=True, blockers=9, approved=True),
        row("few", blockers=1, confirmed=1),
        row("many", blockers=1, confirmed=3),
        row("blocked", blockers=4, confirmed=4),
        row("diff", disagreement=True, blockers=0, confirmed=5),
    ]
    assert [r.id for r in triage.order(rows)] == [
        "diff",
        "blocked",
        "few",
        "many",
        "done",
    ]


def test_search_is_literal_and_filters_status():
    import json
    from pathlib import Path

    from kinderbuch_bildlabor import search

    record = json.loads(Path("sammlung/genovefa/scan_022.json").read_text("utf-8"))
    records = {"a": record}
    both = ("offen", "strittig", "endbestätigt")
    assert search.search(records, "TREPPE", both)
    assert not search.search(records, "Treppe", ("endbestätigt",))
    record["image_description"]["working_description_de"] = "Thür und Tür"
    assert [h[2] for h in search.search(records, "thür", both)] == ["Thür und Tür"]
    assert [h[2] for h in search.search(records, "tür", both)] == ["Thür und Tür"]
    assert not search.search(records, "thuer", both)
