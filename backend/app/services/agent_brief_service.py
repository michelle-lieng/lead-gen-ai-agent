"""
Turns one plain-English instruction from the chat into the structured
configuration the existing pipeline requires.

Two entry points:

* ``draft_lead_brief`` writes a project's ``query_search_target`` and
  ``lead_minimum_criteria`` from a sentence like "dental clinics in Sydney",
  so lead collection needs no manual setup.
* ``draft_enrichment`` creates a fully configured :class:`Enrichment` from a
  sentence like "does this clinic have more than one doctor?". The column
  shape is unchanged — only who fills it in.
"""

import logging
import re
from contextlib import contextmanager
from typing import Literal, Optional

import openai
from pydantic import BaseModel, Field

from .. import exceptions
from ..models.tables import Enrichment
from ..prompts.agent_briefs import ENRICHMENT_DRAFT_PROMPT, LEAD_BRIEF_PROMPT
from ..utils.ai_clients import build_openai_client
from .enrichment_service import enrichment_service
from .project_service import project_service

logger = logging.getLogger(__name__)

MODEL = "gpt-5-mini"

# No sampling parameters are passed with it. gpt-5-class models reject
# `temperature` outright — "Unsupported parameter: 'temperature' is not
# supported with this model" — and a 400 here fails the whole run at its first
# step. Shape these drafts through the prompts instead.

# Reserved so a drafted column can never collide with the merged_results base
# columns or the reasoning/evidence siblings the execution service appends.
RESERVED_COLUMNS = {"id", "project_id", "lead", "serp_count"}


class LeadBriefDraft(BaseModel):
    """What the model returns for a 'find me leads like this' instruction."""

    query_search_target: str = Field(
        description="Expanded description of the organisations to search for"
    )
    lead_minimum_criteria: str = Field(
        description="The minimum test a name must pass to count as a lead"
    )
    num_queries: int = Field(
        default=4, description="How many distinct search queries this target deserves"
    )


class EnrichmentDraft(BaseModel):
    """What the model returns for an 'answer this about every lead' instruction."""

    enrichment_name: str
    column_name: str
    result_format: Literal["True/False", "Number", "Text"]
    goal: str
    acceptable_evidence: str
    result_true_if: str = ""
    result_false_if: str = ""
    result_number_value: str = ""
    result_text_value: str = ""


def _slugify_column(value: str, fallback: str) -> str:
    """Coerce a model-supplied column name into a valid SQL identifier."""
    slug = re.sub(r"[^a-z0-9_]+", "_", (value or "").strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug or slug[0].isdigit():
        slug = f"col_{slug}" if slug else fallback
    return slug[:40].rstrip("_") or fallback


def _uniquify(value: str, taken: set[str], *, limit: int) -> str:
    """Append _2, _3 ... until `value` is free, respecting a length limit."""
    if value not in taken:
        return value
    for suffix in range(2, 100):
        tail = f"_{suffix}"
        candidate = f"{value[: limit - len(tail)].rstrip('_')}{tail}"
        if candidate not in taken:
            return candidate
    raise ValueError(f"Could not find a free name based on '{value}'")


@contextmanager
def _openai_errors(step: str):
    """
    Turn an OpenAI failure into an AppError the API can answer with.

    Every other service that calls the model does this; this one did not, so a
    rejected key or an unsupported parameter escaped as an unhandled exception.
    That is worse than it sounds: unhandled exceptions are answered outside the
    CORS layer, so the browser discards the response and the SPA reports a
    server that is answering perfectly well as unreachable.
    """
    try:
        yield
    except openai.AuthenticationError as exc:
        raise exceptions.ApiKeyNotConfiguredError(
            "OpenAI rejected your API key. Check the key entered via the “API keys” button."
        ) from exc
    except openai.PermissionDeniedError as exc:
        raise exceptions.OpenAIRequestError(
            f"OpenAI refused this request ({step}): {exc}. "
            "Your key may not have access to the model this app uses."
        ) from exc
    except openai.RateLimitError as exc:
        raise exceptions.OpenAIRequestError(
            f"OpenAI is rate-limiting or out of quota ({step}): {exc}"
        ) from exc
    except openai.BadRequestError as exc:
        message = str(exc).lower()
        if "token" in message and ("limit" in message or "reduce" in message or "maximum" in message):
            raise exceptions.OpenAITokenLimitExceededError() from exc
        raise exceptions.OpenAIRequestError(f"OpenAI rejected the request ({step}): {exc}") from exc
    except openai.APIConnectionError as exc:
        raise exceptions.OpenAIRequestError(
            f"Could not reach OpenAI ({step}): {exc}"
        ) from exc
    except openai.OpenAIError as exc:
        raise exceptions.OpenAIRequestError(f"OpenAI call failed ({step}): {exc}") from exc


class AgentBriefService:
    """Drafts pipeline configuration from natural-language instructions."""

    def draft_lead_brief(
        self, project_id: int, instruction: str, *, openai_api_key: str
    ) -> dict:
        """
        Expand a one-line instruction into the project's search configuration
        and persist it, so query generation can run immediately afterwards.

        Returns the drafted fields plus the recommended query count.
        """
        project_service.get_project(project_id)  # raises if the project is gone

        client = build_openai_client(openai_api_key)
        with _openai_errors("drafting the lead brief"):
            response = client.responses.parse(
                model=MODEL,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You configure a lead-generation pipeline. You translate a "
                            "user's short instruction into a precise search target and a "
                            "strict test for what counts as a lead. You never broaden or "
                            "narrow what the user asked for."
                        ),
                    },
                    {"role": "user", "content": LEAD_BRIEF_PROMPT.format(instruction=instruction)},
                ],
                text_format=LeadBriefDraft,
            )
        draft = response.output_parsed

        num_queries = max(3, min(8, draft.num_queries or 4))
        project_service.update_project(
            project_id,
            query_search_target=draft.query_search_target.strip(),
            lead_minimum_criteria=draft.lead_minimum_criteria.strip(),
        )
        logger.info(f"✅ Drafted lead brief for project {project_id}")

        return {
            "query_search_target": draft.query_search_target.strip(),
            "lead_minimum_criteria": draft.lead_minimum_criteria.strip(),
            "num_queries": num_queries,
        }

    def draft_enrichment(
        self, project_id: int, instruction: str, *, openai_api_key: str
    ) -> Enrichment:
        """
        Create a fully configured enrichment from a one-line instruction.

        The enrichment is created and then completed in a second call because
        ``create_enrichment`` only accepts a name; the update path is where the
        service validates that a configuration is complete.
        """
        project_service.get_project(project_id)  # raises if the project is gone

        client = build_openai_client(openai_api_key)
        with _openai_errors("drafting the field"):
            response = client.responses.parse(
                model=MODEL,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You configure research tasks for an AI agent that can search "
                            "the web and read pages. You write precise goals and evidence "
                            "standards, and you never ask for evidence that could not "
                            "plausibly exist on the public web."
                        ),
                    },
                    {
                        "role": "user",
                        "content": ENRICHMENT_DRAFT_PROMPT.format(instruction=instruction),
                    },
                ],
                text_format=EnrichmentDraft,
            )
        draft = response.output_parsed

        existing = enrichment_service.get_enrichments(project_id)
        taken_names = {e.enrichment_name for e in existing}
        taken_columns = {e.column_name for e in existing if e.column_name} | RESERVED_COLUMNS

        name = _uniquify(
            (draft.enrichment_name or instruction).strip()[:50] or "Enrichment",
            taken_names,
            limit=50,
        )
        column = _uniquify(
            _slugify_column(draft.column_name, fallback="enrichment"),
            taken_columns,
            limit=40,
        )

        config = {
            "column_name": column,
            "goal": draft.goal.strip(),
            "acceptable_evidence": draft.acceptable_evidence.strip(),
            "result_format": draft.result_format,
        }
        if draft.result_format == "True/False":
            config["result_true_if"] = draft.result_true_if.strip() or (
                "The evidence shows the condition in the goal is met."
            )
            config["result_false_if"] = draft.result_false_if.strip() or (
                "The evidence shows the condition in the goal is not met, or no "
                "supporting evidence could be found."
            )
        elif draft.result_format == "Number":
            config["result_number_value"] = draft.result_number_value.strip() or (
                "The figure described in the goal. Return nothing if it cannot be "
                "established from the sources."
            )
        else:
            config["result_text_value"] = draft.result_text_value.strip() or (
                "A short plain-text answer to the goal. Return nothing if it cannot "
                "be established from the sources."
            )

        enrichment = enrichment_service.create_enrichment(
            project_id=project_id,
            enrichment_name=name,
            enrichment_description=instruction.strip(),
        )
        try:
            return enrichment_service.update_enrichment(enrichment.id, **config)
        except Exception:
            # A half-configured enrichment would show as a permanently empty
            # column in the register, so remove it rather than leave it behind.
            logger.exception("❌ Drafted enrichment failed validation; rolling back")
            enrichment_service.delete_enrichment(enrichment.id)
            raise


agent_brief_service = AgentBriefService()
