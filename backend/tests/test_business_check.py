from types import SimpleNamespace

import httpx
import openai
import pytest

from app.exceptions import OpenAIRequestError
from app.services.business_check import BusinessCheck, check_businesses
from app.services.places_service import Place

PLACES = [
    Place("Sydney Harbour", ("natural_feature",)),
    Place("Sydney by Seaplane", ("travel_agency", "establishment")),
    Place("The Rocks", ("tourist_attraction",)),
    Place("Harbourside Hospitality", ("restaurant", "establishment")),
]


class FakeClient:
    """Stands in for the OpenAI client: records the prompt, returns a fixed verdict."""

    def __init__(self, indices=None, error=None):
        self.prompts = []
        self._indices, self._error = indices, error
        self.responses = SimpleNamespace(parse=self._parse)

    def _parse(self, **kwargs):
        self.prompts.append(kwargs["input"][-1]["content"])
        if self._error:
            raise self._error
        return SimpleNamespace(output_parsed=BusinessCheck(business_indices=self._indices))


def test_keeps_only_places_the_model_marks_as_businesses():
    client = FakeClient(indices=[1, 3])
    kept = check_businesses(PLACES, "Companies around Sydney Harbour", openai_api_key="k", client=client)
    assert [p.name for p in kept] == ["Sydney by Seaplane", "Harbourside Hospitality"]


def test_out_of_range_and_repeated_indices_are_ignored():
    client = FakeClient(indices=[3, 3, 9, -1, 1])
    kept = check_businesses(PLACES, "q", openai_api_key="k", client=client)
    assert [p.name for p in kept] == ["Sydney by Seaplane", "Harbourside Hospitality"]


def test_prompt_lists_every_place_with_its_types_and_the_search():
    client = FakeClient(indices=[])
    check_businesses(PLACES, "Companies around Sydney Harbour", openai_api_key="k", client=client)
    prompt = client.prompts[0]
    assert "Companies around Sydney Harbour" in prompt
    assert "0. Sydney Harbour (natural_feature)" in prompt
    assert "3. Harbourside Hospitality (restaurant, establishment)" in prompt


def test_no_places_skips_the_model():
    client = FakeClient(indices=[0])
    assert check_businesses([], "q", openai_api_key="k", client=client) == []
    assert client.prompts == []


def test_model_failure_is_reported_as_an_openai_error():
    error = openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com"))
    with pytest.raises(OpenAIRequestError):
        check_businesses(PLACES, "q", openai_api_key="k", client=FakeClient(error=error))
