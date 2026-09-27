from types import SimpleNamespace as E

from app.services.agent_brief_service import (
    EnrichmentDraft,
    MessagePlan,
    apply_format_override,
    build_plan,
    known_column_names,
)


def test_base_and_criteria_are_kept_separate():
    out = build_plan(
        MessagePlan(find=True, find_instruction="Companies based around Sydney Harbour",
                    criteria=["Does this company invest in environmental causes?"]),
        current_target=None, existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["find"] is True
    assert out["find_instruction"] == "Companies based around Sydney Harbour"
    assert out["criteria"] == ["Does this company invest in environmental causes?"]
    assert out["columns"] == []


def test_plan_without_qualifiers_has_no_criteria():
    out = build_plan(MessagePlan(find=True, find_instruction="Dental clinics in Sydney"),
                     current_target=None, existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["criteria"] == []


def test_criteria_matching_existing_columns_are_dropped():
    out = build_plan(
        MessagePlan(criteria=["Invests in environmental causes", "Has 50+ staff?"]),
        current_target="x", existing_columns=["invests in environmental causes"],
        unanswered_by_name={}, enrichments=[])
    assert out["criteria"] == ["Has 50+ staff?"]


def test_empty_base_falls_back_to_current_target():
    out = build_plan(MessagePlan(find=True, find_instruction="  ", criteria=["Q?"]),
                     current_target="Companies around Sydney Harbour",
                     existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["find_instruction"] == "Companies around Sydney Harbour"


def test_find_with_no_base_and_no_target_is_dropped():
    out = build_plan(MessagePlan(find=True, find_instruction=""), current_target=None,
                     existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["find"] is False and out["find_instruction"] == ""


def test_new_columns_are_capped_at_five():
    out = build_plan(MessagePlan(criteria=[f"C{i}?" for i in range(4)], columns=[f"R{i}" for i in range(4)]),
                     current_target="x", existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert len(out["criteria"]) + len(out["columns"]) == 5
    assert out["criteria"] == ["C0?", "C1?", "C2?", "C3?"]  # criteria take priority


def test_format_override_forces_true_false():
    d = EnrichmentDraft(enrichment_name="Env", column_name="env", result_format="Text",
                        goal="g", acceptable_evidence="e")
    assert apply_format_override(d, "True/False").result_format == "True/False"
    assert apply_format_override(d, None).result_format == "Text"



def test_known_column_names_include_the_question_each_was_drafted_from():
    question = "Does this company invest in or financially support environmental causes?"
    enrichments = [
        E(enrichment_name="Invests in Environmental Causes", enrichment_description=question),
        E(enrichment_name="Website", enrichment_description=None),
    ]
    names = known_column_names(enrichments)
    out = build_plan(
        MessagePlan(find=True, find_instruction="Companies based around Sydney Harbour",
                    criteria=[question]),
        current_target="x", existing_columns=names, unanswered_by_name={}, enrichments=[])
    assert out["criteria"] == []
    assert "Website" in names


def test_location_is_passed_through_for_a_search():
    out = build_plan(MessagePlan(find=True, find_instruction="Companies based around Sydney Harbour",
                                 location=" Sydney Harbour "),
                     current_target=None, existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["location"] == "Sydney Harbour"


def test_location_is_dropped_when_nothing_is_searched():
    out = build_plan(MessagePlan(location="Sydney", columns=["Website"]),
                     current_target=None, existing_columns=[], unanswered_by_name={}, enrichments=[])
    assert out["location"] == ""
