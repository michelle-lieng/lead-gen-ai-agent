from types import SimpleNamespace as E

from app.services.column_gaps import unanswered_columns, unanswered_leads

ROWS = [
    {"lead": "A", "env": True, "env_reasoning": "found report"},
    {"lead": "B", "env": None, "env_reasoning": "searched, nothing found"},
    {"lead": "C", "env": None, "env_reasoning": None},
    {"lead": "D", "env": "", "env_reasoning": "  "},
]


def test_researched_leads_with_no_answer_are_not_unanswered():
    assert unanswered_leads(ROWS, "env") == ["C", "D"]


def test_unanswered_columns_lists_only_columns_with_gaps():
    ens = [E(id=1, enrichment_name="Env", column_name="env"),
           E(id=2, enrichment_name="Web", column_name="web"),
           E(id=3, enrichment_name="Draft", column_name=None)]
    rows = [dict(r, web="x.com", web_reasoning="r") for r in ROWS]
    assert unanswered_columns(rows, ens) == [
        {"enrichment_id": 1, "name": "Env", "column_name": "env", "leads": ["C", "D"]}]
