"""
Google Places: businesses in a named location, found directly on Google Maps.

Used before the web search when a chat message names a place. Only the name,
business status and types are requested (all on the Pro SKU); adding website, phone or rating would move
every request to the Enterprise SKU, which has a fifth of the free monthly
allowance.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import httpx
from sqlalchemy.exc import SQLAlchemyError

from ..exceptions import DatabaseFailureError, GooglePlacesRequestError
from ..models.tables import MergedResult, SerpLead, SerpUrl
from ..utils.lead_utils import normalize_lead_name

logger = logging.getLogger(__name__)

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = "places.displayName,places.businessStatus,places.types,nextPageToken"
PAGE_SIZE = 20  # Google's maximum per page; results stop at 60 in total


def places_query(instruction: str, location: str) -> str:
    """The text sent to Google: the search, with its place added if it lacks one."""
    instruction, location = instruction.strip(), location.strip()
    if location and location.lower() not in instruction.lower():
        return f"{instruction} in {location}"
    return instruction


# Types Google gives places that are not businesses: areas, addresses, natural
# features and public parks. A text search for "companies around Sydney
# Harbour" also returns the harbour itself, the suburbs around it and its
# parks; none of them is a lead. Business types never overlap with these.
# tourist_attraction is deliberately absent: tour operators carry it too.
NOT_A_BUSINESS = frozenset({
    "political", "geocode", "country", "colloquial_area", "postal_code", "postal_town",
    "route", "street_address", "school_district",
    "administrative_area_level_1", "administrative_area_level_2", "administrative_area_level_3",
    "administrative_area_level_4", "administrative_area_level_5", "administrative_area_level_6",
    "administrative_area_level_7",
    "locality", "neighborhood", "sublocality", "sublocality_level_1", "sublocality_level_2",
    "sublocality_level_3", "sublocality_level_4", "sublocality_level_5",
    "natural_feature", "beach", "island", "lake", "mountain_peak", "nature_preserve", "river",
    "scenic_spot", "woods",
    "park", "national_park", "state_park", "city_park", "botanical_garden", "dog_park", "garden",
})


@dataclass(frozen=True)
class Place:
    name: str
    # Google's types, e.g. ("restaurant", "establishment"); context for the
    # business check.
    types: tuple[str, ...] = ()


def parse_places(payload: dict) -> list[Place]:
    """Businesses from one response page: no closed, nameless or non-business places."""
    places = []
    for item in payload.get("places") or []:
        name = ((item.get("displayName") or {}).get("text") or "").strip()
        if not name or item.get("businessStatus") == "CLOSED_PERMANENTLY":
            continue
        types = tuple(item.get("types") or ())
        if NOT_A_BUSINESS.intersection(types):
            continue
        places.append(Place(name=name, types=types))
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


def source_link(query: str) -> str:
    """The source row a Places search is recorded under, one per query."""
    return f"google-places:{query}"


def save_places(project_id: int, query: str, places: list[Place]) -> dict:
    """
    Save businesses from one Places search as leads.

    They go through the same path as web-extracted leads (serp_leads, then
    aggregation, then merged_results), so a business found both ways is one
    row whose Sources count includes Google.
    """
    # Imported here so the pure helpers above load without the whole search
    # pipeline (and its OpenAI agents) behind leads_serp_service.
    from .database_service import db_service
    from .leads_serp_service import leads_serp_service
    from .merged_results_service import merged_results_service
    from .project_service import project_service

    distinct = new_place_names(places, set())
    try:
        with db_service.get_session() as session:
            link = source_link(query)
            source = (
                session.query(SerpUrl)
                .filter(SerpUrl.project_id == project_id, SerpUrl.link == link)
                .first()
            )
            if source is None:
                source = SerpUrl(
                    project_id=project_id,
                    query=query,
                    title="Google Places",
                    link=link,
                    snippet=f"Businesses Google Maps lists for {query!r}",
                    status="processed",
                )
                session.add(source)
                session.flush()

            already_linked = {
                lead
                for (lead,) in session.query(SerpLead.lead).filter(
                    SerpLead.serp_url_id == source.id
                )
            }
            in_table = {
                lead
                for (lead,) in session.query(MergedResult.lead).filter(
                    MergedResult.project_id == project_id
                )
            }
            for name, _ in new_place_names(places, already_linked):
                session.add(SerpLead(project_id=project_id, serp_url_id=source.id, lead=name))
            session.commit()

        leads_serp_service._transform_leads_to_aggregated(project_id)
        merged_results_service.merge_serp_leads(project_id)

        project_service.update_project_counts_from_db(project_id)
    except SQLAlchemyError as e:
        logger.exception(f"❌ Error saving Google Places results for project {project_id}")
        raise DatabaseFailureError("Failed to save Google Places results") from e

    new = sum(1 for name, _ in distinct if name not in in_table)
    return {
        "found": len(distinct),
        "new": new,
        "existing": len(distinct) - new,
        "leads": [name for name, _ in distinct],
    }
