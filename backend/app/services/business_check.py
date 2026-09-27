"""
An AI check that each Google Places result is a business, not just a place.

The type filter in places_service drops what Google itself labels as areas,
natural features and parks. Much still gets through: landmarks, precincts and
wharves typed only as "tourist_attraction" or "point_of_interest". One model
call over the whole result list decides the rest from the names and types.
"""

import logging

from pydantic import BaseModel, Field

from ..prompts.agent_briefs import BUSINESS_CHECK_PROMPT
from ..utils.ai_clients import build_openai_client
from .agent_brief_service import MODEL, _openai_errors
from .places_service import Place

logger = logging.getLogger(__name__)


class BusinessCheck(BaseModel):
    """What the model returns: which numbered places are businesses."""

    business_indices: list[int] = Field(default_factory=list)


def check_businesses(
    places: list[Place],
    query: str,
    *,
    openai_api_key: str,
    client=None,
) -> list[Place]:
    """Keep only the places the model judges to be businesses, in their order."""
    if not places:
        return []
    listing = "\n".join(
        f"{index}. {place.name}" + (f" ({', '.join(place.types)})" if place.types else "")
        for index, place in enumerate(places)
    )
    client = client or build_openai_client(openai_api_key)
    with _openai_errors("checking which Google results are businesses"):
        response = client.responses.parse(
            model=MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You sort Google Maps results into businesses and plain places "
                        "for a lead-generation tool. You only judge what is listed."
                    ),
                },
                {
                    "role": "user",
                    "content": BUSINESS_CHECK_PROMPT.format(query=query, places=listing),
                },
            ],
            text_format=BusinessCheck,
        )
    keep: set[int] = {
        index
        for index in response.output_parsed.business_indices
        if 0 <= index < len(places)
    }
    kept = [place for index, place in enumerate(places) if index in keep]
    logger.info(f"✅ Business check kept {len(kept)} of {len(places)} places for {query!r}")
    return kept
