"""
Enrichment Execution Service - Uses OpenAI Agent with SERP and Web Scraper tools
to enrich company data based on user-defined fields.
"""

import asyncio
import re
from typing import Literal, Optional
from pydantic import Field, create_model
from agents import Agent, Runner, function_tool, set_default_openai_key, ModelSettings
from agents.exceptions import MaxTurnsExceeded
from openai.types.shared import Reasoning
import logging
import openai

from ..models.tables import Enrichment
from .job_service import job_service
# Import existing Jina functions from utils
from ..utils.scrapers import jina_serp_scraper, jina_url_scraper
from ..config import settings
from ..exceptions import (
    ApiKeyNotConfiguredError,
    OpenAITokenLimitExceededError,
    ExternalScraperError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class EnrichmentExecutionService:
    """Service for executing enrichment operations using AI agents"""

    def __init__(self):
        """Initialize the enrichment execution service"""
        # Track Jina API calls for cost tracking (per instance)
        self.jina_serp_calls = 0
        self.jina_url_calls = 0

        # Set up OpenAI API key if available
        if settings.openai_api_key:
            set_default_openai_key(settings.openai_api_key)

        # Separate semaphores for each API type since they have different rate limits
        # and are used in different workflow stages
        self.serp_scraper_semaphore = asyncio.Semaphore(
            15
        )  # For jina_serp_scraper (increased from 10)
        self.url_scraper_semaphore = asyncio.Semaphore(
            15
        )  # For jina_url_scraper (increased from 10, Jina Reader API: 200 RPM)
        self.llm_semaphore = asyncio.Semaphore(
            3
        )  # For Runner.run (OpenAI API, reduced from 12 due to TPM limits: 30K TPM)

    def _create_tools(self):
        """
        Create tool functions that can be used by the agent.
        These are wrapper functions that don't include 'self' in their signature.
        """

        @function_tool
        async def jina_serp_search(search_phrase: str) -> list[dict]:
            """
            Search the web using Jina SERP API. Returns a list of search results.
            Use this tool to find information about a company when you need to search for it.

            Args:
                search_phrase: The search query (e.g., "Hurstville Highpoint Medical Centre more than 1 doctor")
                    CRITICAL: Use ONLY simple, natural language queries. DO NOT use:
                    - site: operators (e.g., "site:example.com" - these cause errors)
                    - Quotes around terms (e.g., "Locations" "Bondi" - these cause errors)
                    - Complex boolean operators (AND, OR, NOT)
                    - Parentheses or special syntax
                    Instead, use plain natural language like: "98 Training gym locations list"
                    Keep queries short (under 10 words) and simple.

            Returns:
                List of dictionaries containing search results with keys like 'title', 'snippet', 'url'
            """
            self.jina_serp_calls += 1
            try:
                async with self.serp_scraper_semaphore:
                    results = await jina_serp_scraper(search_phrase)
                logger.info(f"SERP search successful: {len(results)} results")
                return results
            except Exception as e:
                logger.error(f"SERP search error: {e}")
                return []

        @function_tool
        async def jina_scrape_url(url: str) -> str:
            """
            Scrape a URL using Jina API to get the full content of a webpage.
            Use this tool when you need more detailed information from a specific webpage.

            Args:
                url: The URL to scrape (e.g., "https://example.com")

            Returns:
                String containing the scraped and cleaned content of the webpage
            """
            self.jina_url_calls += 1
            try:
                async with self.url_scraper_semaphore:
                    content = await jina_url_scraper(url)
                logger.info(f"URL scrape successful: {url}")
                return content
            except Exception as e:
                logger.error(f"URL scrape error for {url}: {e}")
                return "scrape_failed"

        return [jina_serp_search, jina_scrape_url]

    def _extract_metadata(self, result) -> dict:
        """Extract metadata from the Runner result including tool calls and costs."""
        # Estimate Jina costs (SERP: ~$0.01 per search, URL: ~$0.01 per URL)
        serp_cost = self.jina_serp_calls * 0.01
        url_cost = self.jina_url_calls * 0.01

        return {
            "tool_calls": {
                "jina_serp_search": self.jina_serp_calls,
                "jina_scrape_url": self.jina_url_calls,
                "total": self.jina_serp_calls + self.jina_url_calls,
            },
            "jina_costs": {
                "serp_calls": self.jina_serp_calls,
                "url_calls": self.jina_url_calls,
                "estimated_cost_usd": serp_cost + url_cost,
            },
        }

    def _create_enrichment_output_model(
        self, enrichment_name: str, output_type: Literal["str", "int", "bool"]
    ):
        """
        Dynamically create a Pydantic model for the enrichment output.
        Returns a model with three fields: enrichment_name, enrichment_name_reasoning, enrichment_name_evidence
        """

        # Determine the type annotation based on output_type
        if output_type == "int":
            value_type = Optional[int]
        elif output_type == "bool":
            value_type = Optional[bool]
        else:  # str
            value_type = Optional[str]

        # Create the model dynamically
        EnrichmentOutput = create_model(
            "EnrichmentOutput",
            **{
                enrichment_name: (
                    value_type,
                    Field(
                        default=None,
                        description=f"The enriched value for {enrichment_name}",
                    ),
                ),
                f"{enrichment_name}_reasoning": (
                    str,
                    Field(
                        default="",
                        description=f"Brief explanation of how the {enrichment_name} value was determined",
                    ),
                ),
                f"{enrichment_name}_evidence": (
                    str,
                    Field(
                        default="",
                        description=f"Evidence or source that supports the {enrichment_name} value",
                    ),
                ),
            },
        )

        return EnrichmentOutput

    def _build_enrichment_prompt(
        self,
        company_name: str,
        enrichment_name: str,
        output_type: Literal["str", "int", "bool"],
        prompt_goal: str,
        prompt_reasoning: str,
        string_prompt: str = "",
        is_false_prompt: str = "",
        is_true_prompt: str = "",
        int_prompt: str = "",
    ) -> str:
        """
        Build a dynamic prompt based on user inputs for the enrichment task.
        """
        # Determine type-specific values
        if output_type == "str":
            json_value_example = "string value or None"
            null_handling = "If the company name doesn't match exactly in search results, return None. If you cannot find the information, set the value to None and explain why in the reasoning. If the company is completely irrelevant to the question (e.g., asking about gym locations for a transportation company), return None."
            type_specific_instructions = f"""String extraction instructions: {string_prompt}
Output type: String (text value)
"""
        elif output_type == "int":
            json_value_example = "integer value or None"
            null_handling = "If the company name doesn't match exactly in search results, return None. If you cannot find the information, set the value to None and explain why in the reasoning. If the company is completely irrelevant to the question (e.g., asking about gym locations for a transportation company), return None - do NOT apply the rules to irrelevant companies."
            type_specific_instructions = f"""Integer extraction instructions: {int_prompt}
Output type: Integer (whole number)
"""
        elif output_type == "bool":
            json_value_example = "true/false or None"
            null_handling = "If the company name doesn't match exactly OR the company is completely irrelevant to the question, return None. If you search and find no evidence of the condition being true (but company matches and is relevant), return false. Only return None if company name doesn't match exactly, company is irrelevant, or you truly cannot determine anything."
            type_specific_instructions = f"""True condition: {is_true_prompt}
False condition: {is_false_prompt}
Output type: Boolean (true/false)

Important for boolean fields:
- If you search and find evidence that the condition is TRUE, return true
- If you search and find evidence that the condition is FALSE, return false
- If you search and find NO evidence of the condition being true, return false (not None)
- Only return None if you truly cannot determine anything (e.g., no relevant information found at all, wrong company, etc.)
"""

        base_prompt = f"""You are an AI assistant that enriches company data by finding specific information about companies.

Your task:
1. Find information about the company: {company_name}
2. Extract the requested enrichment field based on the goal and instructions below
3. Return the value along with your reasoning and evidence

Goal: {prompt_goal}

Additional context: {prompt_reasoning}

"""

        base_prompt += f"""
Instructions:
1. **First, use jina_serp_search** to search for information about the company and the enrichment field
   - **CRITICAL: Use ONLY simple, natural language queries** - plain text like "company name location information"
   - **DO NOT use site: operators** (e.g., "site:example.com") - these cause 422 errors
   - **DO NOT use quotes** around terms (e.g., "Locations" "Bondi") - these cause 422 errors
   - **DO NOT use boolean operators** (AND, OR, NOT) or parentheses
   - Use natural language queries that a person would type into Google (5-10 words max)
   - Example: "98 Training gym locations" NOT "site:98training.com \"Locations\" \"Bondi\""
2. **Review the search results carefully** - check if the snippets and titles already contain the information you need
3. **Search thoroughly and interpret evidence broadly**:
   - Use multiple search queries if needed to find comprehensive information
   - Consider related evidence that may be relevant depending on the question
   - Look for company pages, reports, and documentation that might contain the information
   - Don't be too literal - consider the broader context and related information
4. **Distinguish between directory listings and actual company information**:
   - **Directory listings** (e.g., listings of multiple businesses/entities in an area) are NOT evidence about the specific company - they just list multiple entities
   - **Actual company pages** show information specifically about that company (e.g., official website, company profile, company-specific pages)
5. **Decide whether to scrape URLs based on information sufficiency**:
   - **If SERP results clearly answer the question**: Extract the answer directly from snippets/titles - DO NOT scrape URLs
   - **Only scrape when necessary**: Scrape URLs only when you need additional information that isn't available in the SERP results
   - **When scraping, optimize for relevance**: Choose the URL(s) most likely to contain the answer (e.g., official company website, company profile page, relevant company pages)
   - **Be thorough but efficient**: If you're unsure about the answer after reviewing SERP results, scrape the relevant URL(s) to get definitive information rather than guessing
6. Extract the exact value for the enrichment field based on the output type ({output_type})
7. Provide clear reasoning explaining how you determined the value
8. Include evidence (URLs, quotes, or specific data points) that support your answer

Important:
- **CRITICAL: Company name must match exactly** - If the company name in search results doesn't match exactly (e.g., searching for "Uber" but results are about a different company), return None. Do NOT apply enrichment rules if the company name doesn't match.
- **CRITICAL: Irrelevant companies return None** - If the company is completely irrelevant to the enrichment question (e.g., asking about gym locations for a transportation company like Uber, or asking about medical practices for a retail company), return None. Do NOT try to apply the enrichment rules to irrelevant companies - return None with clear reasoning that the company is not relevant to the question.
- **Work efficiently within turn limits** - you have 10 turns maximum. Use tools strategically and avoid unnecessary calls
- **Use tools efficiently and sparingly** - each API call has a cost and uses a turn
- **Prioritize search result snippets** - if they clearly answer the question, use them directly without scraping
- **Scrape when information is insufficient** - if SERP results don't provide enough information to answer confidently, scrape the most relevant URL(s) to get definitive information
- **Optimize URL selection** - choose the most relevant source (e.g., official company website, company profile page, relevant company pages) that's most likely to contain the answer
- **Search comprehensively but efficiently** - use 2-3 targeted search queries maximum, then decide if scraping is needed
- **Interpret evidence broadly** - consider related information and broader context, not just exact literal matches
- **If you can't find the answer after reasonable searches, return None with clear reasoning** - don't keep searching indefinitely
- Be precise and accurate
- **None handling**: {null_handling}
- Always cite your sources in the evidence field

Output JSON:
You must return a JSON object with the following structure:
In {enrichment_name} return None if you do not find any information at all, OR if the company is irrelevant to the question. Do not make up information! Do not apply enrichment rules to irrelevant companies - return None instead.

{type_specific_instructions}
{{
    "{enrichment_name}": {json_value_example},
    "{enrichment_name}_reasoning": "<explanation>",
    "{enrichment_name}_evidence": "<sources/URLs>"
}}
"""

        return base_prompt

    def _truncate_by_word_count(self, text: str, max_words: int) -> str:
        """
        Truncate text to max_words, cutting at word boundaries.

        Using gpt-5-mini which has 500,000 TPM limit (16.7x higher than gpt-4.1's 30K TPM)
        - ~1.3 tokens per word on average
        - With 500K TPM, we can handle much larger requests (50K+ tokens per request)
        - Safe target: ~50,000 tokens for content = ~38,000 words
        - Still need to leave room for prompt, instructions, and output (~10-15K tokens)
        - Truncation is a safety mechanism for per-request context window limits
        """
        if not text:
            return text

        words = text.split()
        if len(words) <= max_words:
            return text

        # Truncate to max_words and rejoin
        truncated_words = words[:max_words]
        return " ".join(truncated_words) + "\n\n[Content truncated due to token limit]"

    async def enrich_company(
        self,
        company_name: str,
        enrichment_name: str,
        prompt_goal: str,
        prompt_reasoning: str,
        output_type: Literal["str", "int", "bool"] = "str",
        string_prompt: str = "",
        is_false_prompt: str = "",
        is_true_prompt: str = "",
        int_prompt: str = "",
        return_metadata: bool = False,
    ) -> dict:
        """
        Main function to enrich a company with a specific field.

        Args:
            company_name: Name of the company to enrich
            enrichment_name: Name of the field to enrich (e.g., "more_than_1_doctor")
            prompt_goal: Goal description for the enrichment (required)
            prompt_reasoning: Additional context for the enrichment (required)
            output_type: Type of output expected ("str", "int", or "bool")
            string_prompt: Optional instructions for string extraction
            is_false_prompt: Optional description of false condition for bool
            is_true_prompt: Optional description of true condition for bool
            int_prompt: Optional instructions for integer extraction
            return_metadata: If True, include metadata about tool calls and costs in the result

        Returns:
            Dictionary with enrichment_name, enrichment_name_reasoning, and enrichment_name_evidence.
            If return_metadata=True, also includes "_metadata" key with usage and cost information.
        """
        # Set OpenAI API key for agents SDK
        if not settings.openai_api_key:
            raise ApiKeyNotConfiguredError(
                "OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file."
            )
        set_default_openai_key(settings.openai_api_key)

        # Validate that required prompts are provided based on output type
        if output_type == "str":
            if not string_prompt or not string_prompt.strip():
                raise ValueError(
                    f"string_prompt is required when output_type is 'str'. Please provide string extraction instructions."
                )
        elif output_type == "int":
            if not int_prompt or not int_prompt.strip():
                raise ValueError(
                    f"int_prompt is required when output_type is 'int'. Please provide integer extraction instructions."
                )
        elif output_type == "bool":
            if not is_true_prompt or not is_true_prompt.strip():
                raise ValueError(
                    f"is_true_prompt is required when output_type is 'bool'. Please provide a description of the true condition."
                )
            if not is_false_prompt or not is_false_prompt.strip():
                raise ValueError(
                    f"is_false_prompt is required when output_type is 'bool'. Please provide a description of the false condition."
                )

        # Reset counters before run
        self.jina_serp_calls = 0
        self.jina_url_calls = 0

        # Create output model
        OutputModel = self._create_enrichment_output_model(enrichment_name, output_type)

        # Build prompt
        instructions = self._build_enrichment_prompt(
            company_name=company_name,
            enrichment_name=enrichment_name,
            output_type=output_type,
            prompt_goal=prompt_goal,
            prompt_reasoning=prompt_reasoning,
            string_prompt=string_prompt,
            is_false_prompt=is_false_prompt,
            is_true_prompt=is_true_prompt,
            int_prompt=int_prompt,
        )

        # Create tools that don't include 'self' in their signature
        tools = self._create_tools()

        # Create agent with tools
        agent = Agent(
            name="Company Enrichment Agent",
            instructions=instructions,
            tools=tools,
            output_type=OutputModel,
            model="gpt-5-mini",  # Using gpt-5-mini: 500K TPM, better quality, supports function tools, 10x cheaper input than gpt-4o
            model_settings=ModelSettings(
                reasoning=Reasoning(
                    effort="minimal"
                ),  # Lower latency - custom function tools work with minimal effort
                verbosity="low",
            ),
        )

        # Run the agent with max_turns for enrichment (default is 10)
        input_text = (
            f"Company to enrich: {company_name}\nEnrichment field: {enrichment_name}"
        )

        # Retry logic: 3 retries max, parse wait time from error message
        max_retries = 3
        default_wait_time = 10.0  # Fallback if we can't parse the time

        # Track original input for truncation if needed
        original_input_text = input_text
        current_input_text = input_text

        result = None
        for attempt in range(max_retries):
            try:
                async with self.llm_semaphore:
                    result = await Runner.run(
                        agent, input=current_input_text, max_turns=10
                    )
                break  # Success, exit retry loop

            except (TimeoutError, openai.APITimeoutError) as e:
                # Timeout errors from OpenAI API
                if attempt < max_retries - 1:
                    wait_time = min(
                        2.0 * (2**attempt), 30.0
                    )  # Exponential backoff: 2s, 4s, 8s (max 30s)
                    logger.warning(
                        f"⚠️ Timeout error for {company_name} enrichment (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {wait_time:.1f}s before retry..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
            except openai.RateLimitError as e:
                # Rate limit errors - retry with parsed wait time
                if attempt < max_retries - 1:
                    error_str = str(e)
                    wait_time = default_wait_time
                    # Try to parse the retry time from the error message
                    retry_time_match = re.search(
                        r"Please try again in ([\d.]+)s", error_str, re.IGNORECASE
                    )
                    if retry_time_match:
                        try:
                            parsed_time = float(retry_time_match.group(1))
                            wait_time = max(parsed_time + 1.0, 2.0)  # Minimum 2 seconds
                        except ValueError:
                            # Invalid float format (e.g., "1.2.3"), use default
                            pass  # wait_time already set to default_wait_time
                    else:
                        # Try to match milliseconds
                        retry_time_match = re.search(
                            r"Please try again in ([\d.]+)ms", error_str, re.IGNORECASE
                        )
                        if retry_time_match:
                            try:
                                parsed_time_ms = float(retry_time_match.group(1))
                                parsed_time = parsed_time_ms / 1000.0
                                wait_time = max(parsed_time + 1.0, 2.0)
                            except ValueError:
                                # Invalid float format, use default
                                pass  # wait_time already set to default_wait_time

                    logger.warning(
                        f"⚠️ Rate limit error for {company_name} enrichment (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {wait_time:.1f}s before retry..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
            except openai.BadRequestError as e:
                # Check if it's a "request too large" error (truncate and retry)
                error_str = str(e)
                error_lower = error_str.lower()
                is_request_too_large = (
                    "request too large" in error_lower
                    or "tokens must be reduced" in error_lower
                    or "maximum context length" in error_lower
                    or "token limit" in error_lower
                )

                if is_request_too_large and attempt < max_retries - 1:
                    # With gpt-5-mini's 500K TPM, we can handle much larger content
                    # ~38K words = ~50K tokens, leaving ~10-15K tokens for prompt/instructions/output
                    max_words = 38000  # Increased significantly from 10K to take advantage of 500K TPM
                    word_count = len(current_input_text.split())
                    if word_count > max_words:
                        current_input_text = self._truncate_by_word_count(
                            current_input_text, max_words
                        )
                        logger.warning(
                            f"⚠️ Request too large for {company_name} enrichment (attempt {attempt + 1}/{max_retries}). "
                            f"Truncating from {word_count} words to {max_words} words and retrying..."
                        )
                        await asyncio.sleep(1.0)
                        continue
                    else:
                        # Already at or below limit, can't truncate further
                        logger.error(
                            f"❌ Request too large for {company_name} enrichment even with {word_count} words. "
                            f"Error: {error_str}"
                        )
                        raise OpenAITokenLimitExceededError(
                            f"Request too large: input exceeds token limit even after truncation. {error_str}"
                        )
                else:
                    # Not a "request too large" error, or max retries reached
                    raise

        if result is None:
            raise RuntimeError(f"Failed to get result after {max_retries} attempts")

        # Extract and convert output to dictionary
        output = result.final_output
        output_dict = output.model_dump()

        # Add metadata if requested
        if return_metadata:
            metadata = self._extract_metadata(result)
            metadata["prompt"] = instructions
            output_dict["_metadata"] = metadata

        return output_dict

    async def enrich_leads(
        self, enrichment: Enrichment, 
        leads_data: list[dict], 
        project_id: int, 
        enrichment_id: int, 
        job_id: int
    ) -> tuple[list[dict], list[str]]:
        """
        Process leads enrichment using the enrichment configuration.

        Args:
            enrichment: The enrichment configuration
            leads_data: List of lead dictionaries e.g. [{"lead": "Acme Corp", "serp_count": 5, "bcorp_certified": True}, {...}, ...]
            project_id: Project ID to enrich leads for
        Returns:
            Tuple of (enriched_leads, columns)
        """
        try:
            # Map result_format to output_type for AI service
            output_type_map = {"True/False": "bool", "Text": "str", "Number": "int"}
            output_type = output_type_map.get(enrichment.result_format)
            column_name = enrichment.column_name
            
            leads_to_enrich = []
            already_enriched_leads = []

            for lead_row in leads_data:
                company_name = lead_row.get("lead", "")
                if not company_name:
                    # Skip leads without a "lead" field
                    continue
                # Check if this lead already has a non-NULL/non-empty value for column_name
                existing_value = lead_row.get(column_name)
                
                # Consider None, empty string, or missing key as "needs enrichment"
                # Consider any other value (including False, 0, empty list) as "already enriched"
                if existing_value is None or existing_value == "" or column_name not in lead_row:
                    leads_to_enrich.append(lead_row)
                else:
                    already_enriched_leads.append(lead_row)

            # Process each lead to enrich
            enriched_leads = []
            for lead_row in leads_to_enrich:
                company_name = lead_row.get("lead", "")
                
                try:
                    # Run enrichment for this company
                    result = await self.enrich_company(
                        company_name=company_name,
                        enrichment_name=column_name,
                        prompt_goal=enrichment.goal,
                        prompt_reasoning=enrichment.acceptable_evidence,
                        output_type=output_type,
                        string_prompt=enrichment.result_text_value or "",
                        is_false_prompt=enrichment.result_false_if or "",
                        is_true_prompt=enrichment.result_true_if or "",
                        int_prompt=enrichment.result_number_value or "",
                        return_metadata=False
                    )
                    
                    # Create enriched lead row
                    enriched_lead = lead_row.copy()
                    
                    # Extract the enrichment value, reasoning, and evidence from result
                    enriched_lead[column_name] = result.get(column_name, "")
                    enriched_lead[f"{column_name}_reasoning"] = result.get(f"{column_name}_reasoning", "")
                    enriched_lead[f"{column_name}_evidence"] = result.get(f"{column_name}_evidence", "")
                    
                    enriched_leads.append(enriched_lead)
                    
                except (
                    ExternalScraperError,
                    OpenAITokenLimitExceededError,
                    ApiKeyNotConfiguredError,
                    TimeoutError,
                    openai.APITimeoutError,
                    openai.RateLimitError,
                    openai.BadRequestError,
                    RuntimeError,
                    MaxTurnsExceeded,
                ) as e:
                    # They will propagate up to indicate bugs that need fixing
                    logger.exception(
                        f"❌ Failed to enrich '{company_name}' for column '{column_name}'. "
                        f"Error: {type(e).__name__}: {str(e)}"
                    )
                    
                    # Add the lead with NULL values - keep business data clean
                    # Error details are in logs, not in business data
                    enriched_lead = lead_row.copy()
                    enriched_lead[column_name] = None
                    enriched_lead[f"{column_name}_reasoning"] = None
                    enriched_lead[f"{column_name}_evidence"] = None
                    enriched_leads.append(enriched_lead)
            
            # Get columns list
            columns = list(enriched_leads[0].keys()) if enriched_leads else ["lead"]
            # Ensure enrichment columns are in the list
            if column_name not in columns:
                columns.append(column_name)
            if f"{column_name}_reasoning" not in columns:
                columns.append(f"{column_name}_reasoning")
            if f"{column_name}_evidence" not in columns:
                columns.append(f"{column_name}_evidence")
            
            # Mark job as completed
            job_service.mark_job_as_completed(job_id)
            return (enriched_leads, columns)
        except Exception as e:
            print("Marking job as failed")
            # Handle any unexpected errors in the overall function
            logger.exception(
                f"❌ Unexpected error in enrich_leads for column '{enrichment.column_name}'. "
                f"Error: {type(e).__name__}: {str(e)}"
            )
            # Mark job as failed
            job_service.mark_job_as_failed(job_id, f"Unexpected error: {type(e).__name__}: {str(e)}")
            # Return empty results on critical failure
            return ([], ["lead"])


# Global service instance
enrichment_execution_service = EnrichmentExecutionService()
