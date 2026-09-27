import pytest

from app.models.schemas import EnrichmentCreate
from app.models.tables import BUILT_IN_RESULT_COLUMNS
from app.services.places_service import places_query


def test_no_address_column_is_built_in():
    # Google addresses are not stored; a research column may be called anything
    # address-like, including "address".
    assert not any("address" in name for name in BUILT_IN_RESULT_COLUMNS)
    assert EnrichmentCreate(enrichment_name="Address", column_name="address").column_name == "address"


@pytest.mark.parametrize("name", ["lead", "serp_count", "id", "project_id"])
def test_built_in_columns_cannot_be_research_columns(name):
    with pytest.raises(ValueError):
        EnrichmentCreate(enrichment_name="X", column_name=name)


def test_places_query_adds_the_location_when_missing():
    assert places_query("Companies that fund the environment", "Sydney Harbour") == (
        "Companies that fund the environment in Sydney Harbour"
    )


def test_places_query_keeps_an_instruction_that_already_names_the_place():
    assert places_query("Companies based around Sydney Harbour", "sydney harbour") == (
        "Companies based around Sydney Harbour"
    )


def test_places_query_without_location_is_unchanged():
    assert places_query("Gyms in Brisbane", "") == "Gyms in Brisbane"
