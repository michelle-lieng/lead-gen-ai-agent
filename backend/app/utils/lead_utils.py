"""
Lead utility functions for normalizing and processing lead names
"""
import re
import unicodedata

# Common legal suffixes and noise words
LEGAL_SUFFIXES = [
    "pty", "ltd", "pty ltd", "limited", "inc", "inc.", "corp",
    "corporation", "co", "co.", "gmbh", "llc", "plc", "sa", "bv",
    "ag", "kg", "srl", "spa", "oy", "ab"
]

# Convert to regex OR (e.g. r"\b(pty|ltd|inc|...)$") 
LEGAL_SUFFIXES_REGEX = r"\b(?:{})\b".format("|".join([re.escape(s) for s in LEGAL_SUFFIXES]))

def sanitize_value(value: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '', value).lower()

def normalize_lead_name(name: str) -> str:
    """
    Clean and normalize company names for deduplication.
    Inspired by: https://medium.com/dnb-data-science-hub/company-name-matching
    
    Steps:
    1. Unicode normalization (NFKD)
    2. Lowercase
    3. Remove punctuation and symbols
    4. Remove legal suffixes (pty, ltd, inc, llc, co, gmbh, etc.)
    5. Collapse extra whitespace
    6. Remove zero-width and invisible unicode
    """

    if not name:
        return ""

    # Convert to string
    name = str(name)

    # 1. Unicode normalization (removes accents; “Crédit” -> “credit”)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ASCII", "ignore").decode("ASCII")

    # 2. Lowercase
    name = name.lower()

    # 3. Remove punctuation & special symbols
    name = re.sub(r"[^a-z0-9\s]", " ", name)

    # 4. Remove legal suffixes & generic company terms
    # e.g. “Microsoft Pty Ltd” → “microsoft”
    name = re.sub(LEGAL_SUFFIXES_REGEX, " ", name)

    # Remove standalone generic words
    name = re.sub(r"\b(company|companies|holdings?|international)\b", " ", name)

    # 5. Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # 6. Remove zero-width/invisible unicode chars
    name = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", name)

    return name.strip()

if __name__ == "__main__":
    # Example usage / debug runner
    test_names = [
        "Microsoft Pty Ltd",
        "L’Oréal SA",
        "Credit Agricole",
        "Tesla Motors LLC",
        "BlueScope Steel Pty Limited",
        "wagstaff piling pty limited",
        "anewx pty ltd",
        "austral construction pty ltd",
        "avopiling group pty ltd",
        "bauer foundations australia pty. ltd.",
        "cf group piling pty ltd",
        "geotech pty ltd",
        "gfwa pty ltd",
        "trevi australia pty. ltd.",
        "mcmillan contracting pty ltd",
        "brc piling & foundations",
        "bridgepro engineering pty ltd"
    ]

    for name in test_names:
        print(f"{name} -> {normalize_lead_name(name)}")
