"""
Resume section detection and segmentation.

Breaks a resume's raw text into an ordered list of labeled sections
(contact, summary, skills, experience, education, projects, ...) so downstream
scoring can evaluate depth per section instead of treating the whole resume as
one blob. Detection uses a "short line + header keyword" heuristic; long
sentences that merely mention a keyword ("5 years of experience") do not
become headers.
"""
import re

# Canonical section kinds in display order.
SECTION_KINDS = (
    "contact",
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
    "certifications",
    "languages",
    "awards",
    "publications",
    "volunteering",
    "interests",
    "references",
)

# header keyword -> kind (a line matching any keyword is that kind).
_HEADER_KEYWORDS = {
    "contact": [
        "contact", "contact information", "personal details",
        "personal information", "personal info",
    ],
    "summary": [
        "professional summary", "career summary", "summary", "profile",
        "objective", "career objective", "about me", "about",
    ],
    "skills": [
        "technical skills", "skills & technologies", "skills and technologies",
        "skills & expertise", "core competencies", "technical competencies",
        "technical skillset", "technologies", "skills",
    ],
    "experience": [
        "work experience", "professional experience", "work history",
        "career history", "professional background", "employment history",
        "internships", "relevant experience", "experience",
    ],
    "education": [
        "academic background", "educational background", "education",
        "academics", "qualifications", "academic qualifications",
    ],
    "projects": [
        "project work", "personal projects", "academic projects",
        "major projects", "key projects", "portfolio", "projects",
    ],
    "certifications": [
        "professional certifications", "certifications & training",
        "certifications & licenses", "credentials", "certifications",
        "certificates", "licenses", "licenses & certifications",
    ],
    "languages": ["language proficiency", "languages"],
    "awards": ["awards & honors", "awards & achievements", "awards", "honors",
               "honours", "achievements", "distinctions"],
    "publications": ["publications", "research", "research & publications"],
    "volunteering": ["volunteer experience", "volunteer work", "volunteering",
                     "volunteer", "community service", "community"],
    "interests": ["interests", "hobbies", "extracurricular", "activities"],
    "references": ["professional references", "references"],
}

# Compile each keyword set into one alternation.
_HEADER_PATTERNS = {
    kind: re.compile(
        r"\b(?:%s)\b" % "|".join(re.escape(k) for k in keywords),
        re.IGNORECASE,
    )
    for kind, keywords in _HEADER_KEYWORDS.items()
}

# A line is only a header if it's short, OR the keyword sits near the start.
_MAX_HEADER_WORDS = 8
_HEADER_KEYWORD_FRONT = 2


def _classify_line(line):
    """Return the section kind for a candidate header line, or None."""
    stripped = line.strip().strip(".:\t ").rstrip(".:\t ")
    if not stripped:
        return None

    words = [w for w in stripped.split() if w]
    if not words:
        return None

    n = len(words)
    low = stripped.lower()

    for kind, pattern in _HEADER_PATTERNS.items():
        match = pattern.search(low)
        if not match:
            continue
        front = match.start()
        front_word_index = len(low[:front].split()) if front else 0
        # Header if line is short, or the keyword is among the first words.
        if n <= 3 or front_word_index < _HEADER_KEYWORD_FRONT:
            return kind

    return None


def detect_sections(text):
    """
    Return an ordered list of dicts:
        {"kind", "header", "content"}
    Content is the joined raw lines that follow the header until the next one.
    """
    if not text:
        return []

    sections = []
    current = None  # {"kind", "header", "lines"}

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue

        kind = _classify_line(stripped)
        if kind is not None:
            if current is not None:
                current["content"] = "\n".join(current.pop("lines"))
                sections.append(current)
            current = {"kind": kind, "header": stripped, "lines": []}
        elif current is not None:
            current["lines"].append(stripped)

    if current is not None:
        current["content"] = "\n".join(current.pop("lines"))
        sections.append(current)

    return sections


def get_section(text, kind):
    """Return the content of the first section of `kind`, or None."""
    for section in detect_sections(text):
        if section["kind"] == kind:
            return section["content"]

    return None


def has_section(text, kind):
    """True if a section of `kind` was detected."""
    return get_section(text, kind) is not None


def section_coverage(text):
    """Return a dict mapping each kind -> bool (present/absent)."""
    present = {s["kind"] for s in detect_sections(text)}
    return {kind: kind in present for kind in SECTION_KINDS}