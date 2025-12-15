"""
Enrichment Agent - Uses OpenAI Agent with SERP and Web Scraper tools
to enrich company data based on user-defined fields.
"""
import asyncio
from typing import Literal, Optional
from pydantic import Field, create_model
from agents import Agent, Runner, function_tool, set_default_openai_key
import logging

# Import existing Jina functions from utils
from app.utils.scrapers import jina_serp_scraper, jina_url_scraper
from app.config import settings
from app.exceptions import ApiKeyNotConfiguredError

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Track Jina API calls for cost tracking
_jina_serp_calls = 0
_jina_url_calls = 0

# Wrap existing functions as tools for the agent
@function_tool
async def jina_serp_search(search_phrase: str) -> list[dict]:
    """
    Search the web using Jina SERP API. Returns a list of search results.
    Use this tool to find information about a company when you need to search for it.
    
    Args:
        search_phrase: The search query (e.g., "Hurstville Highpoint Medical Centre number of doctors")
    
    Returns:
        List of dictionaries containing search results with keys like 'title', 'snippet', 'url'
    """
    global _jina_serp_calls
    _jina_serp_calls += 1
    try:
        results = await jina_serp_scraper(search_phrase)
        logging.info(f"SERP search successful: {len(results)} results")
        return results
    except Exception as e:
        logging.error(f"SERP search error: {e}")
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
    global _jina_url_calls
    _jina_url_calls += 1
    try:
        content = await jina_url_scraper(url)
        logging.info(f"URL scrape successful: {url}")
        return content
    except Exception as e:
        logging.error(f"URL scrape error for {url}: {e}")
        return "scrape_failed"


def extract_metadata(result) -> dict:
    """Extract metadata from the Runner result including tool calls and costs."""
    # Estimate Jina costs (SERP: ~$0.01 per search, URL: ~$0.01 per URL)
    serp_cost = _jina_serp_calls * 0.01
    url_cost = _jina_url_calls * 0.01
    
    return {
        "tool_calls": {
            "jina_serp_search": _jina_serp_calls,
            "jina_scrape_url": _jina_url_calls,
            "total": _jina_serp_calls + _jina_url_calls
        },
        "jina_costs": {
            "serp_calls": _jina_serp_calls,
            "url_calls": _jina_url_calls,
            "estimated_cost_usd": serp_cost + url_cost
        }
    }


def create_enrichment_output_model(enrichment_name: str, output_type: Literal["str", "int", "bool"]):
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
        'EnrichmentOutput',
        **{
            enrichment_name: (value_type, Field(
                default=None,
                description=f"The enriched value for {enrichment_name}"
            )),
            f"{enrichment_name}_reasoning": (str, Field(
                default="",
                description=f"Brief explanation of how the {enrichment_name} value was determined"
            )),
            f"{enrichment_name}_evidence": (str, Field(
                default="",
                description=f"Evidence or source that supports the {enrichment_name} value"
            ))
        }
    )
    
    return EnrichmentOutput


def build_enrichment_prompt(
    company_name: str,
    enrichment_name: str,
    output_type: Literal["str", "int", "bool"],
    prompt_goal: str,
    prompt_reasoning: str,
    string_prompt: str = "",
    is_false_prompt: str = "",
    is_true_prompt: str = "",
    int_prompt: str = ""
) -> str:
    """
    Build a dynamic prompt based on user inputs for the enrichment task.
    """
    # Determine type-specific values
    if output_type == "str":
        json_value_example = 'string value or None'
        null_handling = "If you cannot find the information, set the value to None and explain why in the reasoning."
        type_specific_instructions = f"""String extraction instructions: {string_prompt}
Output type: String (text value)
"""
    elif output_type == "int":
        json_value_example = 'integer value or None'
        null_handling = "If you cannot find the information, set the value to None and explain why in the reasoning."
        type_specific_instructions = f"""Integer extraction instructions: {int_prompt}
Output type: Integer (whole number)
"""
    elif output_type == "bool":
        json_value_example = 'true/false or None'
        null_handling = "If you search and find no evidence of the condition being true, return false (not None). Only return None if you truly cannot determine anything."
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
- **Use tools efficiently and sparingly** - each API call has a cost
- **Prioritize search result snippets** - if they clearly answer the question, use them directly without scraping
- **Scrape when information is insufficient** - if SERP results don't provide enough information to answer confidently, scrape the most relevant URL(s) to get definitive information
- **Optimize URL selection** - choose the most relevant source (e.g., official company website, company profile page, relevant company pages) that's most likely to contain the answer
- **Search comprehensively** - use multiple search queries if needed, and look for company pages, reports, and documentation that might contain the information
- **Interpret evidence broadly** - consider related information and broader context, not just exact literal matches
- Be precise and accurate
- **None handling**: {null_handling}
- Always cite your sources in the evidence field

Output JSON:
You must return a JSON object with the following structure:
In {enrichment_name} return None if you do not find any information at all. Do not make up information!

{type_specific_instructions}
{{
    "{enrichment_name}": {json_value_example},
    "{enrichment_name}_reasoning": "<explanation>",
    "{enrichment_name}_evidence": "<sources/URLs>"
}}
"""
    
    return base_prompt


async def enrich_company(
    company_name: str,
    enrichment_name: str,
    prompt_goal: str,
    prompt_reasoning: str,
    output_type: Literal["str", "int", "bool"] = "str",
    string_prompt: str = "",
    is_false_prompt: str = "",
    is_true_prompt: str = "",
    int_prompt: str = "",
    return_metadata: bool = False
) -> dict:
    """
    Main function to enrich a company with a specific field.
    
    Args:
        company_name: Name of the company to enrich
        enrichment_name: Name of the field to enrich (e.g., "number_of_doctors")
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
        raise ApiKeyNotConfiguredError("OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.")
    set_default_openai_key(settings.openai_api_key)
    
    # Validate that required prompts are provided based on output type
    if output_type == "str":
        if not string_prompt or not string_prompt.strip():
            raise ValueError(f"string_prompt is required when output_type is 'str'. Please provide string extraction instructions.")
    elif output_type == "int":
        if not int_prompt or not int_prompt.strip():
            raise ValueError(f"int_prompt is required when output_type is 'int'. Please provide integer extraction instructions.")
    elif output_type == "bool":
        if not is_true_prompt or not is_true_prompt.strip():
            raise ValueError(f"is_true_prompt is required when output_type is 'bool'. Please provide a description of the true condition.")
        if not is_false_prompt or not is_false_prompt.strip():
            raise ValueError(f"is_false_prompt is required when output_type is 'bool'. Please provide a description of the false condition.")
    
    # Create output model
    OutputModel = create_enrichment_output_model(enrichment_name, output_type)
    
    # Build prompt
    instructions = build_enrichment_prompt(
        company_name=company_name,
        enrichment_name=enrichment_name,
        output_type=output_type,
        prompt_goal=prompt_goal,
        prompt_reasoning=prompt_reasoning,
        string_prompt=string_prompt,
        is_false_prompt=is_false_prompt,
        is_true_prompt=is_true_prompt,
        int_prompt=int_prompt
    )
    
    # Create agent with tools
    agent = Agent(
        name="Company Enrichment Agent",
        instructions=instructions,
        tools=[jina_serp_search, jina_scrape_url],
        output_type=OutputModel,
    )
    
    # Reset counters before run
    global _jina_serp_calls, _jina_url_calls
    _jina_serp_calls = 0
    _jina_url_calls = 0
    
    # Run the agent
    input_text = f"Company to enrich: {company_name}\nEnrichment field: {enrichment_name}"
    result = await Runner.run(agent, input=input_text)
    
    # Extract and convert output to dictionary
    output = result.final_output
    output_dict = output.model_dump()
    
    # Add metadata if requested
    if return_metadata:
        metadata = extract_metadata(result)
        metadata["prompt"] = instructions
        output_dict["_metadata"] = metadata
    
    return output_dict

# Example usage
async def main():
    """Example of how to use the enrichment agent"""
    #company_to_enrich = "Hurstville Highpoint Medical Centre"
    #company_to_enrich = "Dr Jimmy Nguyen"
    company_to_enrich = "Vital Health Medical"
    enrichment_name = "has_more_than_one_doctor"
    
    # Configure the enrichment
    result = await enrich_company(
        company_name=company_to_enrich,
        enrichment_name=enrichment_name,
        prompt_goal="Find if this medical center has more than 1 doctor",
        prompt_reasoning="Check what doctors work at the clinic and list them.",
        output_type="bool",  # or "str" or "int"
        is_false_prompt="Has only one doctor working at the clinic.",
        is_true_prompt="Has more than one doctor working at the clinic",
        return_metadata=True  # Include metadata about costs and tool usage
    )
    #company_to_enrich = "Schroders Capital"
    # company_to_enrich = "KKR Australia"
    # enrichment_name = "interest_in_mining_tech"
    # result = await enrich_company(
    #     company_name=company_to_enrich,
    #     enrichment_name=enrichment_name,
    #     prompt_goal="Find if this angel investor has previous/existing investments in mining technology in Australia",
    #     prompt_reasoning="Check their current and historical investment portfolio.",
    #     output_type="bool",  # or "str" or "int"
    #     is_false_prompt="Has not invested in mining technology.",
    #     is_true_prompt="Has invested in mining technology.",
    #     return_metadata=True  # Include metadata about costs and tool usage
    # )

    
    print("\n" + "="*50)
    print("ENRICHMENT RESULTS")
    print("="*50)
    for key, value in result.items():
        if key != "_metadata":
            print(f"{key}: {value}")
    print("="*50)
    
    # Display metadata if available
    if "_metadata" in result:
        metadata = result["_metadata"]
        print("\n" + "="*50)
        print("USAGE METADATA")
        print("="*50)
        print(f"Tool Calls:")
        print(f"  - jina_serp_search: {metadata['tool_calls']['jina_serp_search']}")
        print(f"  - jina_scrape_url: {metadata['tool_calls']['jina_scrape_url']}")
        print(f"  - Total: {metadata['tool_calls']['total']}")
        print(f"\nJina API Usage:")
        print(f"  - SERP calls: {metadata['jina_costs']['serp_calls']}")
        print(f"  - URL calls: {metadata['jina_costs']['url_calls']}")
        print(f"  - Estimated cost: ${metadata['jina_costs']['estimated_cost_usd']:.4f}")
        if 'prompt' in metadata:
            print(f"\nPrompt:")
            print("-" * 50)
            print(metadata['prompt'])
            print("-" * 50)
        print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
