import streamlit as st
from api.base import ApiError, NetworkError

# -------------------------------------------------------------------
# Friendly messages for domain error codes (backend -> user-friendly)
# -------------------------------------------------------------------

FRIENDLY_TEMPLATES: dict[str, str] = {
    # Projects
    "DUPLICATE_PROJECT_NAME": "❌ Project name '{project_name}' already exists. Please choose a different name and try again.",
    "PROJECT_NOT_FOUND": "That project can’t be found. It may have been deleted—try refreshing.",
    "INVALID_PROJECT_CONFIGURATION": "This project’s configuration is invalid. Please review the settings.",

    # Dataset / files
    "INVALID_FILE": "That file looks invalid (empty, wrong type, or corrupted). Please upload a valid file.",
    "INVALID_ENRICHMENT_COLUMN": "Your enrichment column selection is invalid. Please check the required columns.",
    "PROJECT_DATASET_NOT_FOUND": "That dataset can’t be found. It may have been removed—try refreshing.",

    # URLs
    "URL_NOT_FOUND": "That URL entry can’t be found. It may have been deleted—try refreshing.",
    "DUPLICATE_URL": "That URL is already in this project.",

    # Infrastructure
    "DATABASE_FAILURE": "Database error. Please try again. If it keeps happening, the server may be down.",
    "API_KEY_NOT_CONFIGURED": "Server configuration issue: an API key is missing. Please contact the admin.",

    # External APIs
    "EXTERNAL_SCRAPER_ERROR": "Scraper service is having issues right now. Please try again in a moment.",
    "OPENAI_TOKEN_LIMIT_EXCEEDED": "This request is too large for the AI to process. Try fewer URLs or smaller content.",

    # Enrichment
    "DUPLICATE_ENRICHMENT_NAME": "That enrichment name already exists. Please choose a different name.",
    "DUPLICATE_COLUMN_NAME": "That column name already exists. Please choose a different column name.",
    "ENRICHMENT_NOT_FOUND": "That enrichment can't be found. It may have been deleted—try refreshing.",
    "EMPTY_ENRICHMENT_FIELD": "The following fields cannot be empty or whitespace only: '{field_names_str}'. Please fill in all required fields.",
    "INCOMPLETE_ENRICHMENT_CONFIG": "Result format '{result_format}' requires the following fields to be filled: '{fields_str}'",
    "NO_LEADS_TO_ENRICH": "Cannot run enrichment: no leads provided. Please add leads before running enrichment.",

    # Generic / server fallback
    "UNEXPECTED_INTERNAL_ERROR": "Something went wrong on the server. Please try again.",
}

# Optionally: status-based fallbacks (for cases with no code)
STATUS_FALLBACK_MESSAGES: dict[int, str] = {
    400: "Bad request. Please check your input and try again.",
    401: "You’re not authenticated. Please log in again.",
    403: "You don’t have permission to do that.",
    404: "Not found.",
    409: "Conflict. This item may already exist.",
    413: "Request too large. Try reducing the input size.",
    422: "Some inputs are invalid. Please correct them and try again.",
    500: "Server error. Please try again.",
    502: "Upstream service error. Please try again soon.",
    503: "Service temporarily unavailable. Please try again soon.",
    504: "Request timed out. Please try again.",
}

def show_network_error(e: NetworkError | None = None):
    # You can also log e somewhere if you want
    st.error("❌ Can't reach the backend. Check BACKEND_URL, server status, or your network/VPC.")


def show_validation_errors(detail: list):
    """
    FastAPI 422 detail format:
      [{"loc": [...], "msg": "...", "type": "..."}]
    """
    error_lines = ["❌ Please fix the highlighted input errors:"]
    for item in detail:
        loc = " → ".join(str(x) for x in item.get("loc", []))
        msg = item.get("msg", "Invalid value")
        error_lines.append(f"- **{loc}**: {msg}")
    
    st.error("\n".join(error_lines))

def friendly_message(e: ApiError) -> str:
    """
    Returns a user-friendly message based on e.code.
    If the template contains placeholders, fill them from e.meta.
    """
    if not e.code:
        return str(e)

    template = FRIENDLY_TEMPLATES.get(e.code)
    if not template:
        # Unknown code: fall back to server-provided detail
        return f"❌ {e.code}: {str(e)}"

    meta = e.meta or {}
    try:
        return template.format(**meta)
    except KeyError:
        # Missing meta placeholders: return template as-is
        return template

def show_api_error(e: ApiError, *, show_debug: bool = False):
    """
    Central place to render API errors in Streamlit.
    - Handles FastAPI 422 field errors
    - Uses your backend error codes for friendly UX
    """

    # 1) Validation errors (422 with list detail)
    if e.status_code == 422 and isinstance(e.detail, list):
        show_validation_errors(e.detail)
        return

    # 2) Code-based message (preferred)
    if e.code:
        st.error(friendly_message(e))
    else:
        # 3) Status fallback
        fallback = STATUS_FALLBACK_MESSAGES.get(e.status_code, "Request failed. Please try again.")
        st.error(f"❌ {fallback}")

    # 4) Optional debug block (nice during dev)
    if show_debug:
        with st.expander("Debug details"):
            st.write({
                "status_code": e.status_code,
                "code": e.code,
                "detail": e.detail,
                "meta": e.meta,
                "url": e.url,
            })