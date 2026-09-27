import pytest

from app.models.schemas import EnrichmentCreate
from app.services.places_service import PLACES_ADDRESS_COLUMN, places_query


def test_address_column_cannot_collide_with_a_research_column():
    # A research column the user names "Address" is slugged to "address"; the
    # Google address must live somewhere no research column can.
    assert PLACES_ADDRESS_COLUMN != "address"
    with pytest.raises(ValueError):
        EnrichmentCreate(enrichment_name="X", column_name=PLACES_ADDRESS_COLUMN)


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
