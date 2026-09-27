"""
Google Places: businesses in a named location, found directly on Google Maps.

Used before the web search when a chat message names a place. Only the Pro
fields are requested (name, address, business status); adding website, phone
or rating would move every request to the Enterprise SKU, which has a fifth of
the free monthly allowance.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from ..exceptions import GooglePlacesRequestError
from ..utils.lead_utils import normalize_lead_name

logger = logging.getLogger(__name__)

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = "places.displayName,places.formattedAddress,places.businessStatus,nextPageToken"
PAGE_SIZE = 20  # Google's maximum per page; results stop at 60 in total


@dataclass(frozen=True)
class Place:
    name: str
    address: str


def parse_places(payload: dict) -> list[Place]:
    """Businesses from one response page, without closed or nameless ones."""
    places = []
    for item in payload.get("places") or []:
        name = ((item.get("displayName") or {}).get("text") or "").strip()
        if not name or item.get("businessStatus") == "CLOSED_PERMANENTLY":
            continue
        places.append(Place(name=name, address=(item.get("formattedAddress") or "").strip()))
    return places


def new_place_names(
    places: list[Place], already_linked: set[str]
) -> list[tuple[str, Place]]:
    """
    (normalized name, place) for each business still to save under a source:
    not already linked to it, and not repeated within this search. Names are
    compared the way leads are merged, so "Blue Cove Pty Ltd" and "BLUE COVE"
    are one business. The first occurrence wins.
    """
    kept = []
    taken = set(already_linked)
    for place in places:
        name = normalize_lead_name(place.name)
        if name and name not in taken:
            taken.add(name)
            kept.append((name, place))
    return kept


def _google_message(response: httpx.Response) -> str:
    try:
        message = (response.json().get("error") or {}).get("message")
    except ValueError:
        message = None
    if message:
        return f"Google Places: {message}"
    return f"Google Places returned HTTP {response.status_code}"


async def search_places(
    query: str,
    api_key: str,
    *,
    client: Optional[httpx.AsyncClient] = None,
    max_pages: int = 3,
) -> list[Place]:
    """Search Google Places, following page tokens up to `max_pages`."""
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=30)
    headers = {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": FIELD_MASK}
    found: list[Place] = []
    seen: set[Place] = set()
    token: Optional[str] = None
    try:
        for _ in range(max_pages):
            body: dict = {"textQuery": query, "pageSize": PAGE_SIZE}
            if token:
                body["pageToken"] = token
            try:
                response = await client.post(PLACES_URL, json=body, headers=headers)
            except httpx.HTTPError as exc:
                raise GooglePlacesRequestError(f"Could not reach Google Places: {exc}") from exc
            if response.status_code >= 400:
                raise GooglePlacesRequestError(_google_message(response))
            payload = response.json()
            for place in parse_places(payload):
                if place not in seen:
                    seen.add(place)
                    found.append(place)
            token = payload.get("nextPageToken")
            if not token:
                break
    finally:
        if owns_client:
            await client.aclose()
    logger.info(f"✅ Google Places found {len(found)} businesses for {query!r}")
    return found
