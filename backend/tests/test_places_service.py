import json
from asyncio import run as asyncio_run

import httpx
import pytest

from app.exceptions import GooglePlacesRequestError
from app.services.places_service import (
    FIELD_MASK,
    PLACES_URL,
    Place,
    new_place_names,
    parse_places,
    search_places,
)


def P(name, status="OPERATIONAL"):
    return {"displayName": {"text": name}, "businessStatus": status}


def test_parse_skips_closed_and_nameless():
    payload = {"places": [P("A"), P("B", status="CLOSED_PERMANENTLY"), {"businessStatus": "OPERATIONAL"}]}
    assert parse_places(payload) == [Place(name="A")]


def test_field_mask_stays_on_the_pro_sku():
    assert "websiteUri" not in FIELD_MASK and "PhoneNumber" not in FIELD_MASK and "rating" not in FIELD_MASK
    # Addresses are not stored, so they are not requested either.
    assert "formattedAddress" not in FIELD_MASK
    assert "places.displayName" in FIELD_MASK and "nextPageToken" in FIELD_MASK


async def run(handler, **kw):
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        return await search_places("Companies around Sydney Harbour", "KEY", client=c, **kw)


def test_follows_page_tokens_up_to_three_pages():
    seen = []

    def handler(req):
        body = json.loads(req.content)
        seen.append(body)
        assert str(req.url) == PLACES_URL and req.headers["X-Goog-Api-Key"] == "KEY"
        assert req.headers["X-Goog-FieldMask"] == FIELD_MASK
        n = len(seen)
        return httpx.Response(200, json={"places": [P(f"Biz {n}")], "nextPageToken": f"t{n}"})

    places = asyncio_run(run(handler))
    assert [p.name for p in places] == ["Biz 1", "Biz 2", "Biz 3"]
    assert "pageToken" not in seen[0] and seen[1]["pageToken"] == "t1" and len(seen) == 3


def test_stops_when_no_next_page():
    def handler(req):
        return httpx.Response(200, json={"places": [P("Only")]})

    assert [p.name for p in asyncio_run(run(handler))] == ["Only"]


def test_google_error_carries_google_message():
    def handler(req):
        return httpx.Response(403, json={"error": {"message": "Places API (New) has not been used in project 123"}})

    with pytest.raises(GooglePlacesRequestError) as err:
        asyncio_run(run(handler))
    assert "Places API (New) has not been used" in str(err.value)


def test_places_already_linked_are_not_saved_twice():
    places = [Place("Harbourside Hospitality Pty Ltd"), Place("Blue Cove")]
    assert [n for n, _ in new_place_names(places, {"harbourside hospitality"})] == ["blue cove"]


def test_duplicate_places_in_one_search_are_saved_once():
    places = [Place("Blue Cove"), Place("BLUE COVE PTY LTD")]
    out = new_place_names(places, set())
    assert [n for n, _ in out] == ["blue cove"] and out[0][1].name == "Blue Cove"


def T(name, *types):
    return {"displayName": {"text": name}, "businessStatus": "OPERATIONAL", "types": list(types)}


def test_parse_skips_places_that_are_not_businesses():
    payload = {"places": [
        T("Sydney Harbour", "natural_feature", "establishment"),
        T("Kirribilli", "locality", "political"),
        T("Neutral Bay", "neighborhood", "political"),
        T("Bradfield Park", "park", "point_of_interest", "establishment"),
        T("Sydney by Seaplane", "tourist_attraction", "travel_agency", "point_of_interest", "establishment"),
        T("Harbourside Hospitality", "restaurant", "point_of_interest", "establishment"),
        {"displayName": {"text": "No Types Pty Ltd"}, "businessStatus": "OPERATIONAL"},
    ]}
    assert [p.name for p in parse_places(payload)] == [
        "Sydney by Seaplane", "Harbourside Hospitality", "No Types Pty Ltd"]


def test_field_mask_requests_types():
    assert "places.types" in FIELD_MASK
