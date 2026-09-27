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


def P(name, address="1 Quay St", status="OPERATIONAL"):
    return {"displayName": {"text": name}, "formattedAddress": address, "businessStatus": status}


def test_parse_skips_closed_and_nameless():
    payload = {"places": [P("A"), P("B", status="CLOSED_PERMANENTLY"), {"formattedAddress": "x"}]}
    assert parse_places(payload) == [Place(name="A", address="1 Quay St")]


def test_field_mask_stays_on_the_pro_sku():
    assert "websiteUri" not in FIELD_MASK and "PhoneNumber" not in FIELD_MASK and "rating" not in FIELD_MASK
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
    places = [Place("Harbourside Hospitality Pty Ltd", "a"), Place("Blue Cove", "b")]
    assert [n for n, _ in new_place_names(places, {"harbourside hospitality"})] == ["blue cove"]


def test_duplicate_places_in_one_search_are_saved_once():
    places = [Place("Blue Cove", "a"), Place("BLUE COVE PTY LTD", "b")]
    out = new_place_names(places, set())
    assert [n for n, _ in out] == ["blue cove"] and out[0][1].address == "a"
