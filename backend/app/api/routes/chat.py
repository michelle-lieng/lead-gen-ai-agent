"""
Chat endpoints: one continuous conversation per project
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from ...services.agent_brief_service import agent_brief_service
from ...services.chat_service import chat_service
from ..deps import ApiKeys, get_api_keys
from ...models.schemas import (
    ChatAppendRequest,
    ChatEntryResponse,
    ChatHistoryResponse,
    InstructionRequest,
    MessagePlanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/projects/{project_id}/chat", response_model=ChatHistoryResponse)
async def get_chat(
    project_id: int,
    before: Optional[int] = None,
    limit: int = Query(200, ge=1, le=500),
):
    """
    Get a page of the project's conversation, oldest first.

    Without `before`, returns the newest `limit` entries. Pass the id of the
    first entry you hold as `before` to page further back.
    """
    entries, has_more = chat_service.get_history(project_id, before, limit)
    return ChatHistoryResponse(
        entries=[ChatEntryResponse.model_validate(e) for e in entries],
        has_more=has_more,
    )


@router.post(
    "/projects/{project_id}/chat",
    response_model=list[ChatEntryResponse],
    status_code=201,
)
async def append_chat(project_id: int, request: ChatAppendRequest):
    """Append entries to the project's conversation, in order"""
    saved = chat_service.append(project_id, request.entries)
    return [ChatEntryResponse.model_validate(e) for e in saved]


@router.post("/projects/{project_id}/chat/interpret", response_model=MessagePlanResponse)
async def interpret_message(
    project_id: int,
    request: InstructionRequest,
    keys: ApiKeys = Depends(get_api_keys),
):
    """
    Decide what one chat message asks for: companies found, research columns
    added, both, or a direct reply. Nothing is run here; the caller runs the
    plan with the existing find and enrich endpoints.
    """
    return agent_brief_service.interpret(
        project_id,
        request.instruction,
        openai_api_key=keys.require_openai(),
    )
