"""
Structural / language-quality signals for a resume.

These feed the ATS scorer's language & formatting categories: strong action
verbs, bullet usage, quantified achievements and consistent date formatting.
All functions are pure string analysis so they never require spaCy.
"""
import re

# Curated strong resume action verbs.
ACTION_VERBS = frozenset({
    "accelerated", "achieved", "analyzed", "architected", "authored",
    "automated", "boosted", "built", "collaborated", "coordinated",
    "created", "cut", "delivered", "deployed", "designed", "developed",
    "drove", "engineered", "established", "executed", "exceeded",
    "generated", "grew", "implemented", "improved", "increased",
    "instituted", "integrated", "launched", "led", "managed", "mentored",
    "migrated", "modernized", "negotiated", "optimized", "orchestrated",
    "organized", "performed", "pioneered", "planned", "presented",
    "produced", "raised", "reduced", "refactored", "scaled", "secured",
    "shipped", "slashed", "spearheaded", "streamlined", "supervised",
    "trained", "transformed", "visualized",
})

_ACTION_VERB_RE = re.compile(
    r"(?<![A-Za-z])%s(?![A-Za-z])" % "|".join(
        sorted(ACTION_VERBS, key=len, reverse=True)
    ),
    re.IGNORECASE,
)

# Lines that begin with a bullet marker (ASCII or Unicode).
_BULLET_RE = re.compile(
    r"^\s*(?:[-*•‣▪▸→>·]|\d{1,2}[.)]|[a-zA-Z][.)])\s+",
)

# A statement is "quantified" if it pairs a number with a metric or currency.
# Currency may prefix the figure ("$1.2M") or follow it ("20%").
_QUANTIFIED_RE = re.compile(
    r"(?:(?:\$|€|£|usd|eur|gbp)[^\S\n]*)?"
    r"\d[\d,.]*[^\S\n]*"
    r"(?:%|percent|million|billion|k\b|m\b|times|"
    r"users|clients|customers|people|employees|revenue|cost|"
    r"conversion|performance|speed|requests|queries|\$|€|£|usd|eur|gbp)",
    re.IGNORECASE,
)

_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

_MONTH_NAME_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\b",
    re.IGNORECASE,
)

# Date range separators: dash variants, "to", or "--".
# Whitespace is restricted to horizontal spaces so matches never cross a
# newline (a date on line N must not absorb the date on line N+1).
_DATE_RANGE_RE = re.compile(
    r"(?P<start>\d{4})[^\S\n]*(?:-|–|—|to|\.{2,})[^\S\n]*"
    r"(?P<end>present|now|\d{4})",
    re.IGNORECASE,
)

_MONTH_DATE_RANGE_RE = re.compile(
    r"(?P<start>(?:\w{3,9}[^\S\n]+)?\d{4})[^\S\n]*(?:-|–|—|to)[^\S\n]*"
    r"(?P<end>present|now|(?:\w{3,9}[^\S\n]+)?\d{4})",
    re.IGNORECASE,
)


def count_action_verbs(text):
    """Count occurrences of strong action verbs in the text."""
    if not text:
        return 0
    return len(_ACTION_VERB_RE.findall(text))


def extract_bullet_lines(text):
    """Return the non-empty lines that start with a bullet marker."""
    if not text:
        return []
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and _BULLET_RE.match(line)
    ]


def count_bullets(text):
    """Number of bullet lines in the text."""
    return len(extract_bullet_lines(text))


def extract_quantified_achievements(text):
    """Return lines that pair a number with a metric or currency.

    Leading bullet markers are stripped so each item is the plain statement.
    """
    if not text:
        return []
    return [
        _BULLET_RE.sub("", line.strip())
        for line in text.splitlines()
        if line.strip() and _QUANTIFIED_RE.search(line)
    ]


def count_quantified_achievements(text):
    """Number of quantified achievement lines."""
    return len(extract_quantified_achievements(text))


def extract_date_ranges(text):
    """
    Return a list of {"start", "end"} date ranges found in the text.

    Handles both "2019 - 2021" and "Jan 2019 - Present" forms.
    """
    if not text:
        return []

    ranges = []

    for match in _MONTH_DATE_RANGE_RE.finditer(text):
        start = match.group("start").strip()
        end = match.group("end").strip()
        ranges.append({"start": start, "end": end})

    for match in _DATE_RANGE_RE.finditer(text):
        start = match.group("start")
        end = match.group("end")
        if not any(
            r["start"].endswith(start) and r["end"].lower() == end.lower()
            for r in ranges
        ):
            ranges.append({"start": start, "end": end})

    return ranges


def extract_years_worked(text):
    """Approximate total years spanned by the date ranges (0 if none)."""
    ranges = extract_date_ranges(text)
    total = 0.0

    for r in ranges:
        start_year = _extract_year(r["start"])
        end_year = (
            2026 if r["end"].lower() in {"present", "now"}
            else _extract_year(r["end"])
        )
        if start_year and end_year and end_year >= start_year:
            total += end_year - start_year

    return round(total, 1)


def _extract_year(value):
    match = _YEAR_RE.search(value)
    return int(match.group(0)) if match else None


def consistent_dates(text):
    """
    True when date usage looks consistent: all four-digit years are plausible
    and either a month-name range exists or all ranges use plain years.
    """
    if not text:
        return True

    years = [int(m) for m in _YEAR_RE.findall(text)]

    if years and not all(1970 <= y <= 2026 for y in years):
        return False

    ranges = extract_date_ranges(text)

    if not ranges:
        return True

    has_month_range = any(
        _MONTH_NAME_RE.search(r["start"]) or _MONTH_NAME_RE.search(r["end"])
        for r in ranges
    )
    has_plain_range = any(
        not _MONTH_NAME_RE.search(r["start"]) and not _MONTH_NAME_RE.search(r["end"])
        for r in ranges
    )

    return not (has_month_range and has_plain_range)