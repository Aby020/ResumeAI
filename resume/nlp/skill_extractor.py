"""
Canonical skill extraction.

Single extractor that replaces the divergent detectors previously scattered
across ats_engine, job_matcher and utils. All matching happens on a canonical
skill name AFTER alias resolution, so JS == JavaScript, ML == Machine Learning,
React.js == React, NodeJS == Node.js and Python3 == Python.
"""
import re

from ..skills import CATEGORY_WEIGHTS, SKILL_CATEGORY_OF, SKILLS
from .aliases import EXTRA_ALIASES

# Ambiguous short skills whose bare form would false-positive against bullet
# markers ("C."), compound names ("C++", "C#"), or English words ("go", "R&D").
# These use compound variants plus a guarded, case-sensitive standalone match.
_AMBIGUOUS = {"C", "R", "Go"}

# A short alphanumeric-only variant is treated as a "bare abbreviation"
# (js, ts, ml, ai, es6...) and guarded so it can't fire inside a compound
# spelling like "react.js" or "next.js" where the abbreviation is just a
# suffix.
_ABBREV_RE = re.compile(r"^[a-z0-9]{1,4}$")

# Single letters must be standalone words: not glued to other letters
# (React != R), not bullet markers ("C."), not "C#" / "C++" / "R&D".
_CASE_SENSITIVE_PATTERNS = {
    "C": re.compile(r"(?<![A-Za-z0-9])C(?![A-Za-z0-9.&#+])"),
    "R": re.compile(r"(?<![A-Za-z0-9])R(?![A-Za-z0-9.&])"),
    "Go": re.compile(r"(?<![A-Za-z0-9])Go(?![A-Za-z0-9])"),
}


def _variants(canonical):
    """Surface spellings for a canonical skill, longest-first."""
    variants = set(EXTRA_ALIASES.get(canonical, ()))
    if canonical not in _AMBIGUOUS:
        variants.add(canonical.lower())
    return sorted((v for v in variants if v), key=len, reverse=True)


def _build_patterns():
    patterns = {}
    for canonical in SKILLS:
        if canonical in _AMBIGUOUS:
            continue
        variants = _variants(canonical)
        if not variants:
            continue

        alternatives = []
        for variant in variants:
            escaped = re.escape(variant)
            if _ABBREV_RE.match(variant):
                # Bare abbreviation: must not be a suffix of a dot/hyphen
                # compound ("react.js", "next.js") — require a clean left edge.
                alternatives.append(r"(?<![\w.])%s" % escaped)
            else:
                alternatives.append(escaped)

        patterns[canonical] = re.compile(
            r"(?<![A-Za-z0-9])(?:%s)(?![A-Za-z0-9])" % "|".join(alternatives),
            re.IGNORECASE,
        )
    return patterns


_PATTERNS = _build_patterns()


def extract_skills(text):
    """
    Extract canonical skills from text.

    Returns a list of dicts, most relevant first:
        {"name", "category", "weight", "count"}
    """
    if not text:
        return []

    counts = {}
    for canonical, pattern in _PATTERNS.items():
        count = len(pattern.findall(text))
        if count:
            counts[canonical] = counts.get(canonical, 0) + count

    for canonical, pattern in _CASE_SENSITIVE_PATTERNS.items():
        if pattern.search(text):
            counts[canonical] = counts.get(canonical, 0) + 1

    skills = []
    for name, count in counts.items():
        category = SKILL_CATEGORY_OF.get(name, "Tools & Platforms")
        skills.append({
            "name": name,
            "category": category,
            "weight": CATEGORY_WEIGHTS.get(category, 0.8),
            "count": count,
        })

    skills.sort(key=lambda s: (s["weight"], s["count"], s["name"]), reverse=True)
    return skills


def canonical_skills(text):
    """Sorted, de-duplicated canonical skill names present in the text."""
    return sorted(s["name"] for s in extract_skills(text))
