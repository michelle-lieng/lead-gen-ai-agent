SERP_QUERIES_PROMPT = """
Generate Google search queries that help discover lists, directories, rankings, or grouped sets of organisations based on the user’s description.

MIXING RULE:
- You may freely mix and recombine ANY attributes, industries, or concepts found in the description — even if the user did not pair them together.
- Any attribute or phrase mentioned anywhere in the description may be combined with any other.

STRICT RULES:
- Use ONLY concepts explicitly mentioned. Do NOT invent new ones.
- ALWAYS assume searches should be in Australia.
- ALWAYS vary location using:
    Australia, Sydney
- Each query must be unique.
- Use natural long-tail Google phrasing (5-10 words).
- No quotes, boolean operators, or run-on sentences.

WHEN DESCRIPTION IS SIMPLE:
- Treat it as the core target and generate variations.

WHEN DESCRIPTION IS LONG OR COMPLEX:
1. Extract all themes, keywords, industries, attributes, values, traits, and initiatives.
2. You may freely mix and match ANY of these to produce diverse angles.
3. Generate location-varied queries for many different combinations.

SUPPORTED QUERY SHAPES:
- “top <theme> in <location>”
- “best <theme> companies in <location>”
- “leading <theme> providers in <location>”
- “<theme> in <location> list”
- “<location> <theme> directory”
- “<theme> companies in <location>”
- “<location> providers for <theme>”
(Use flexibly; you may mix any extracted terms.)

PROCESS:
1. Extract **all** relevant words and phrases from the description.
2. Freely recombine them into different meaningful search targets.
3. Apply the required locations to produce varied, useful Google queries.

Description: {query_search_target}

Generate {num_queries} diverse, mixed, Australia-focused search queries.
"""