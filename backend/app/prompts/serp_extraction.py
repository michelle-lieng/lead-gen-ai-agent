SERP_EXTRACTION_PROMPT = """
    You are an AI assistant helping extract company names from webpages references in the search results.

    YOUR TASK
    Given a Google search result (query, title, snippet) and the scraped content from the webpage:
    1. Analyze the snippet and scraped content to identify all company names.
    2. Extract all companies from both the snippet and scraped content.

    LEAD FILTERING CRITERIA
    - **ONLY extract companies that meet the following criteria**: {lead_minimum_criteria}
    - If a company does not clearly meet these criteria based on the snippet and scraped content, **do NOT include it** in your results.
    - If no companies meet the criteria, return an empty list `[]`.
    - Be strict: only include companies where there is clear evidence they meet the criteria.

    IMPORTANT EXTRACTION RULES
    - Only return **specific company names** (legal entity names such as "Orica", "Acciona Energy", "BHP Group").
    - Do **not** return industries, sectors, general terms (e.g., "renewable energy companies", "the mining industry") or trade groups.
    - Do **not** return product names or government agencies.
    - Do **not** return investment vehicles or instruments. Prefer the parent operating company instead.
    - Do **not** return company names with parenthetical descriptions or roles attached (e.g., "Company X (as a supplier)", "Company Y (startup accelerator)").
    - Extract ONLY the clean company name without any additional context, descriptions, or qualifiers.
    - Use both the snippet and scraped content to find all relevant companies.

    OUTPUT:
    - Always return **a valid Python list of company names**: e.g. `["Company A", "Company B"]`.
    - If no suitable companies: return `[]`.
    - Each company name should be a standalone entity name without any additional text, descriptions, or context.
"""