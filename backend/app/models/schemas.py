"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field, field_validator

from .tables import BUILT_IN_RESULT_COLUMNS
from typing import Optional, Literal


def validate_not_empty_string(v: str) -> str:
    """Shared validation: ensure string is not empty or just whitespace"""
    if not v or not v.strip():
        raise ValueError("Field cannot be empty or whitespace only")
    return v.strip()


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""

    project_name: str
    description: Optional[str] = None

    @field_validator("project_name")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure field is not empty or just whitespace"""
        return validate_not_empty_string(v)


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project"""

    project_name: Optional[str] = None
    description: Optional[str] = None
    query_search_target: Optional[str] = None
    lead_minimum_criteria: Optional[str] = (
        None  # Required if provided, cannot be removed
    )
    leads_collected: Optional[int] = None
    datasets_added: Optional[int] = None
    urls_processed: Optional[int] = None

    @field_validator("lead_minimum_criteria")
    @classmethod
    def validate_lead_minimum_criteria_if_provided(
        cls, v: Optional[str]
    ) -> Optional[str]:
        """If provided as a string, ensure it's not empty or just whitespace. Service layer enforces business rule that prevents removal."""
        if v is not None:  # Only validate if field is being updated (not None)
            return validate_not_empty_string(v)
        return v

    @field_validator("project_name")
    @classmethod
    def validate_not_empty_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """If provided, ensure field is not empty or just whitespace"""
        if v is not None:  # Only validate if field is being updated (not None)
            return validate_not_empty_string(v)
        return v


class ProjectResponse(BaseModel):
    """Schema for project API responses"""

    id: int
    project_name: str
    description: Optional[str] = None
    query_search_target: Optional[str] = None
    lead_minimum_criteria: Optional[str] = (
        None  # Required for new projects and lead extraction, but nullable in DB for backward compatibility
    )
    date_added: str
    last_updated: str
    leads_collected: int
    datasets_added: int
    urls_processed: int

    class Config:
        from_attributes = True

    @field_validator("date_added", "last_updated", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO format string"""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v


class QueryListRequest(BaseModel):
    """Schema for query list requests"""

    queries: list[str]


class QueryGenerationRequest(BaseModel):
    """Schema for AI query generation requests"""

    num_queries: Optional[int] = 3

    @field_validator("num_queries")
    @classmethod
    def validate_num_queries(cls, v: Optional[int]) -> int:
        """Validate num_queries is between 1 and 20"""
        if v is None:
            return 3
        if v < 1 or v > 20:
            raise ValueError("num_queries must be between 1 and 20")
        return v


class UrlCreate(BaseModel):
    """Schema for creating a new production URL"""

    link: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    date: Optional[str] = None  # Optional date from SERP result
    query: Optional[str] = (
        None  # Optional, will default to "Manual Entry" if not provided
    )

    @field_validator("link")
    @classmethod
    def validate_link(cls, v: str) -> str:
        """Ensure link is not empty or just whitespace"""
        return validate_not_empty_string(v)


class UrlUpdate(BaseModel):
    """Schema for updating a production URL"""

    title: Optional[str] = None
    snippet: Optional[str] = None
    date: Optional[str] = None  # Optional date from SERP result
    link: Optional[str] = None

    @field_validator("link")
    @classmethod
    def validate_link_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """If link is provided, ensure it's not empty or just whitespace"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError(
                    "Link cannot be empty or whitespace only. Omit the field if you do not want to update it."
                )
            return v.strip()
        return None


def validate_column_name(v: str) -> str:
    """Validate column name is a valid SQL column name (lowercase, underscores, alphanumeric)"""
    if not v or not v.strip():
        raise ValueError("Column name cannot be empty or whitespace only")
    v = v.strip()
    # Check if it's a valid SQL identifier (lowercase, alphanumeric, underscores only)
    if not v.replace("_", "").isalnum():
        raise ValueError(
            "Column name must contain only lowercase letters, numbers, and underscores"
        )
    if not v.islower():
        raise ValueError("Column name must be lowercase")
    if v[0].isdigit():
        raise ValueError("Column name cannot start with a number")
    if v in BUILT_IN_RESULT_COLUMNS:
        raise ValueError(f"Column name '{v}' is reserved for a built-in column")
    return v


class EnrichmentCreate(BaseModel):
    """Schema for creating a new enrichment"""

    enrichment_name: str
    column_name: Optional[str] = None
    enrichment_description: Optional[str] = None
    # Note: project_id comes from URL path, not request body

    @field_validator("enrichment_name")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure field is not empty or just whitespace"""
        return validate_not_empty_string(v)

    @field_validator("column_name")
    @classmethod
    def validate_column_name_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """Validate column name is a valid SQL column name if provided"""
        if v is not None:
            return validate_column_name(v)
        return v


class EnrichmentUpdate(BaseModel):
    """Schema for updating an enrichment - all fields optional"""

    enrichment_name: Optional[str] = None
    column_name: Optional[str] = None
    enrichment_description: Optional[str] = None
    goal: Optional[str] = None
    acceptable_evidence: Optional[str] = None
    result_format: Optional[str] = None
    result_true_if: Optional[str] = None
    result_false_if: Optional[str] = None
    result_number_value: Optional[str] = None
    result_text_value: Optional[str] = None

    @field_validator("column_name")
    @classmethod
    def validate_column_name_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate column name is a valid SQL identifier if provided"""
        if v is not None and v.strip():
            return validate_column_name(v)
        return v


class EnrichmentResponse(BaseModel):
    """Schema for enrichment API responses"""

    id: int
    project_id: int
    enrichment_name: str
    column_name: Optional[str] = None
    enrichment_description: Optional[str] = None
    goal: Optional[str] = None
    acceptable_evidence: Optional[str] = None
    result_format: Optional[Literal["True/False", "Text", "Number"]] = None
    result_true_if: Optional[str] = None
    result_false_if: Optional[str] = None
    result_number_value: Optional[str] = None
    result_text_value: Optional[str] = None
    date_added: str
    last_updated: str

    class Config:
        from_attributes = True

    @field_validator("date_added", "last_updated", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO format string"""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v


class EnrichLeadsRequest(BaseModel):
    """Schema for enriching leads"""

    leads_data: Optional[list[dict]] = (
        None  # List of lead dictionaries with at least a "lead" key
    )

    @field_validator("leads_data", mode="before")
    @classmethod
    def validate_leads_data(cls, v):
        """Convert None to empty list, ensure it's a list"""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("leads_data must be a list")
        return v


class JobResponse(BaseModel):
    """Schema for job API responses"""

    id: int
    project_id: int
    job_type: str
    job_type_id: Optional[int] = None
    status: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class QueryResponse(BaseModel):
    """Schema for query response"""

    id: int
    project_id: int
    query: str
    date_added: str

    class Config:
        from_attributes = True

    @field_validator("date_added", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO format string"""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v


class UrlResponse(BaseModel):
    """Schema for URL response"""

    id: int
    project_id: int
    query: str
    title: str
    link: str
    snippet: str
    date: Optional[str] = None
    website_scraped: Optional[str] = None
    status: str
    created_at: Optional[str] = None


class UrlGenerationResponse(BaseModel):
    """Schema for URL generation response"""

    urls_added: int
    queries_processed: int


class LeadExtractionResponse(BaseModel):
    """Schema for lead extraction response from SERP URLs"""

    urls_processed: int
    urls_skipped: int
    urls_failed: int
    total_urls_attempted: int
    new_leads_extracted: int
    extracted_leads: list[dict]  # List of extraction results per URL


class MergedResultsResponse(BaseModel):
    """Schema for merged results API response"""

    data: list[dict]  # List of result rows with dynamic columns
    columns: list[str]  # List of column names (base columns + enrichment columns)
    count: int  # Total number of results


class InstructionRequest(BaseModel):
    """One plain-English instruction typed into the chat"""

    instruction: str

    @field_validator("instruction")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure the instruction is not empty or just whitespace"""
        return validate_not_empty_string(v)


class EnrichmentDraftRequest(InstructionRequest):
    """A column to draft from one instruction, optionally with its format pinned"""

    # Criteria columns pass "True/False"; omitted, the drafter picks the format.
    result_format: Optional[Literal["True/False", "Number", "Text"]] = None


class PlacesSearchRequest(BaseModel):
    """One Google Places text search, e.g. 'Companies based around Sydney Harbour'"""

    query: str
    # The place the message names. Added to the query when the query leaves it
    # out, so Google never runs an unanchored, nationwide search.
    location: str = ""

    @field_validator("query")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure the query is not empty or just whitespace"""
        return validate_not_empty_string(v)


class PlacesSearchResponse(BaseModel):
    """What one Google Places search added to the table"""

    found: int  # Distinct businesses kept after the business check
    not_businesses: int = 0  # Google results the AI check judged to be plain places
    new: int  # Of those, how many were not in the table before
    existing: int  # found - new
    leads: list[str]  # Normalized names of every business found


class LeadBriefResponse(BaseModel):
    """The search configuration drafted from a 'find me leads like this' instruction"""

    query_search_target: str
    lead_minimum_criteria: str
    num_queries: int


class MergedRowUpdate(BaseModel):
    """Schema for editing one row of the merged results table"""

    lead: str  # The row's current lead name (its key within the project)
    updates: dict  # Column name -> new value

    @field_validator("lead")
    @classmethod
    def validate_lead(cls, v: str) -> str:
        """Ensure the row key is not empty or just whitespace"""
        return validate_not_empty_string(v)

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, v: dict) -> dict:
        """Ensure at least one column is being written"""
        if not v:
            raise ValueError("At least one column must be provided")
        return v


ChatRole = Literal["user", "agent", "log"]
ChatKind = Literal[
    "text", "step", "result", "error", "breakdown", "definition", "query"
]


class ChatEntryCreate(BaseModel):
    """One entry appended to a project's conversation"""

    role: ChatRole
    kind: ChatKind = "text"
    text: str = ""
    payload: Optional[dict] = None


class ChatAppendRequest(BaseModel):
    """Entries to append, in the order they happened"""

    # Bounded so a single append stays one small transaction
    entries: list[ChatEntryCreate] = Field(min_length=1, max_length=200)


class ChatEntryResponse(BaseModel):
    """One saved entry of a project's conversation"""

    id: int
    project_id: int
    created_at: str
    role: str
    kind: str
    text: str
    payload: Optional[dict] = None

    class Config:
        from_attributes = True

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO format string, marked as UTC"""
        if hasattr(v, "isoformat"):
            return v.isoformat() + ("Z" if v.tzinfo is None else "")
        return v


class ChatHistoryResponse(BaseModel):
    """A page of a project's conversation, oldest first"""

    entries: list[ChatEntryResponse]
    has_more: bool  # True when older entries exist before the first one returned


class ContinueColumn(BaseModel):
    """An existing column to finish for the leads it has no answer for yet"""

    enrichment_id: int
    name: str
    column_name: str
    leads: list[str]  # The leads with no answer yet, in table order


class MessagePlanResponse(BaseModel):
    """What one chat message asks the agent to do"""

    find: bool  # Search for companies (new search or more of the current one)
    find_instruction: str  # The base search: entity type plus its searchable anchor
    location: str  # The place the message names, "" when none; triggers Google Places
    criteria: list[str]  # Yes/No questions, one new True/False column each
    columns: list[str]  # One research question per new column
    continue_columns: list[ContinueColumn]  # Existing columns to finish for unanswered leads
    reply: str  # A direct answer, when the message needs one
