"""
Prompts that turn one plain-English sentence from the chat into the structured
configuration the rest of the pipeline already expects.

The user types "dental clinics in Sydney" or "does this clinic have more than
one doctor?"; these prompts produce the `query_search_target` /
`lead_minimum_criteria` pair and the full enrichment configuration
respectively. No field shapes change — only who fills them in.
"""

LEAD_BRIEF_PROMPT = """
A user of a lead-generation tool typed one short instruction describing the kind of
organisations they want to find. Turn it into two pieces of configuration.

1. `query_search_target` — a richer description of the target used to generate Google
   search queries. Expand the user's instruction into the attributes, industries,
   locations, and traits that would appear in directories, lists, or rankings of these
   organisations. Two to four sentences. Stay strictly inside what the user asked for:
   you may make their intent more explicit, never broader or narrower. Do not invent a
   different industry, a different location, or qualifying criteria they did not imply.

2. `lead_minimum_criteria` — the bare minimum test a name must pass to be recorded as a
   lead. One or two sentences, written as an instruction to an extraction agent reading
   a web page. It should describe the type of entity (e.g. "an individual dental clinic
   or dental practice, not a directory site, association, or franchise head office") and
   any location or attribute constraint the user stated. Be strict: this is the filter
   that keeps rubbish out of the register.

3. `num_queries` — how many distinct search queries this target deserves, from 3 to 8.
   A narrow, single-city, single-industry target needs 3. A broad target spanning several
   industries, attributes, or regions needs more.

Searches are Australia-focused by default. If the user names a location, respect it
exactly; if they name none, assume Australia.

User instruction: {instruction}
"""


ENRICHMENT_DRAFT_PROMPT = """
A user of a lead-generation tool typed one short instruction describing something they
want researched about every company in their list. Turn it into a complete enrichment
configuration for a research agent that can search the web and read pages.

Produce these fields.

- `enrichment_name`: a short human label, title case, at most 50 characters.
  Example: "More than one doctor".

- `column_name`: a valid SQL identifier derived from the name. Lowercase ASCII letters,
  digits and underscores only. Must not start with a digit. At most 40 characters.
  Example: "more_than_one_doctor".

- `result_format`: exactly one of "True/False", "Number", or "Text". Choose by what the
  user actually asked for. A yes/no question is "True/False". A count, price, size, or
  quantity is "Number". Anything else — a name, an address, a description, a category,
  an email, a URL — is "Text".

- `goal`: written to the research agent, telling it precisely what to find out about the
  company. Two to four sentences. Name what to look for and where it is usually found
  (a website's about, team, locations, contact, or services page; a public register; a
  news article). Be concrete about the entity in question.

- `acceptable_evidence`: the reasoning and evidence standard. State what counts as proof
  and what does not. Require evidence tied to the specific company rather than an
  industry generalisation, and say what to do when sources conflict or say nothing.
  Two to four sentences.

Then fill ONLY the fields belonging to the chosen `result_format`, leaving the others
as empty strings.

- If "True/False": `result_true_if` and `result_false_if`, each one or two sentences
  giving an unambiguous condition. They must be genuine opposites covering the whole
  space, so the agent is never stuck between them.
- If "Number": `result_number_value`, defining exactly what is being counted or measured
  and in what unit, and what to return when the figure cannot be established.
- If "Text": `result_text_value`, defining the exact shape of the string to return — its
  format, expected length, and what to return when nothing is found.

Never invent a stricter or looser question than the user asked. Never require evidence
that could not plausibly exist on the public web.

User instruction: {instruction}
"""


INTERPRET_PROMPT = """
You are the agent in a lead-generation tool. The user has one chat per project and
uses it for everything: finding companies (rows) and researching them (columns).
Decide what their newest message asks for.

The project right now:
- Current search target: {search_target}
- Counts as a lead: {lead_criteria}
- Leads in the table: {lead_count}
- Columns so far, with how many leads each is still unanswered for: {columns}

Recent conversation, oldest first:
{history}

Newest message: {message}

Return:

1. `find` — true if the message asks for companies to be found: a new search
   ("dental clinics in Sydney"), or more of the current search ("get me 10 more",
   "find more", "keep going").

2. `find_instruction` — when `find` is true, one standalone sentence describing the
   companies to find. For "more of the same", restate the current search target in a
   sentence. For a new or changed search, describe exactly what the user asked for,
   folding in anything from the conversation it depends on. Empty when `find` is false.

3. `columns` — one entry per piece of information the user wants researched about
   every company ("do they have a franchise?", "find their website", "how many
   staff"). Each entry is a standalone question or instruction, phrased as it would be
   asked about a single company. Never repeat a column that already exists. Empty
   when none is asked for. A single message may ask for both companies and columns.

4. `continue_columns` — names of EXISTING columns (exactly as listed above) the user
   wants finished or resumed for the leads still unanswered: "continue", "keep going",
   "finish the opening hours", "yes" after being asked whether to carry on, or "fill
   in the rest". Only columns that still have unanswered leads. Empty otherwise.

5. `reply` — a short, plain answer only when the message is a question about the
   project or the tool, a greeting, or too unclear to act on (then ask one clarifying
   question). Empty when `find`, `columns` or `continue_columns` already cover the
   message. The reply is only ever words: it must never say that you are doing,
   starting, resuming or will do any work, because a reply alone runs nothing. If the
   user wants work done, put it in the fields above instead.
"""
