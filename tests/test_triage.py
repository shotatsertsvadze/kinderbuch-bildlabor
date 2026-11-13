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
