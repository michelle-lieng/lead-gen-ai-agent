"""
Which research columns still have leads without an answer.

Used when a column is continued, and after a search adds rows, so that every
column ends up filled for every lead. Pure functions: rows in, names out.
"""


def _blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def unanswered_leads(rows: list[dict], column_name: str) -> list[str]:
    """Leads whose column was never researched: no answer and no reasoning.

    A researched lead with no answer found still has its reasoning written, so
    it is not picked up again when the column is continued.
    """
    reasoning = f"{column_name}_reasoning"
    return [
        str(row["lead"])
        for row in rows
        if row.get("lead") and _blank(row.get(column_name)) and _blank(row.get(reasoning))
    ]


def unanswered_columns(rows: list[dict], enrichments: list) -> list[dict]:
    """One entry per column with at least one unanswered lead, in column order."""
    gaps = []
    for enrichment in enrichments:
        if not enrichment.column_name:
            continue
        leads = unanswered_leads(rows, enrichment.column_name)
        if leads:
            gaps.append(
                {
                    "enrichment_id": enrichment.id,
                    "name": enrichment.enrichment_name,
                    "column_name": enrichment.column_name,
                    "leads": leads,
                }
            )
    return gaps
