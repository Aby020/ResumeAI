"""
Entity recognition: degrees, certifications, job titles, companies and
years-of-experience.

Uses spaCy's NER when the model is available (companies, person names) with
deterministic rule-based fallbacks so the pipeline works without it.
"""
import re

from ..skills import SKILL_CATEGORY_OF
from .normalize import _get_nlp
from .sections import get_section

_SKILL_NAME_LOOKUP = {name.lower() for name in SKILL_CATEGORY_OF}

# Ordered (regex, canonical label) pairs. Regexes must be word-anchored enough
# that "Ph.D." does not match inside "mphdocs" and "B.S." matches "B.S." cleanly.
_DEGREE_PATTERNS = (
    (r"(?<![A-Za-z])Ph\.?D\.?", "PhD"),
    (r"(?<![A-Za-z])M\.?Phil\.?", "M.Phil"),
    (r"(?<![A-Za-z])B\.?Tech\b", "B.Tech"),
    (r"(?<![A-Za-z])M\.?Tech\b", "M.Tech"),
    (r"(?<![A-Za-z])B\.?Sc\b", "B.Sc"),
    (r"(?<![A-Za-z])M\.?Sc\b", "M.Sc"),
    (r"(?<![A-Za-z])M\.?B\.?A\b", "MBA"),
    (r"(?<![A-Za-z])B\.?B\.?A\b", "BBA"),
    (r"(?<![A-Za-z])B\.?Com\b", "B.Com"),
    (r"(?<![A-Za-z])M\.?Com\b", "M.Com"),
    (
        r"(?<![A-Za-z])Bachelor(?:'s)?(?: of Science| of Engineering| "
        r"of Technology| of Arts| of Commerce)?\b",
        "Bachelor's",
    ),
    (
        r"(?<![A-Za-z])Master(?:'s)?(?: of Science| of Engineering| "
        r"of Technology| of Arts| of Business Administration)?\b",
        "Master's",
    ),
    (
        r"(?<![A-Za-z])Associate(?:'s(?: Degree)?| degree| of [A-Za-z]+)\b",
        "Associate's",
    ),
    (r"(?<![A-Za-z])Doctorate\b", "Doctorate"),
)

# Two-letter abbreviations collide with English words ("be", "me", "bs") so they
# only count as degrees when written uppercase ("BS", "ME") or dotted ("B.S.").
_TWO_LETTER_DEGREES = (
    ("BS", "B.S"),
    ("BA", "B.A"),
    ("BE", "B.E"),
    ("MS", "M.S"),
    ("MA", "M.A"),
    ("ME", "M.E"),
)

_DEGREE_RES = [
    (re.compile(pattern, re.IGNORECASE), label)
    for pattern, label in _DEGREE_PATTERNS
]

_DEGREE_RES.extend(
    (
        re.compile(rf"(?<![A-Za-z])(?:{letters[0]}\.{letters[1]}|{letters})(?![a-z])"),
        label,
    )
    for letters, label in _TWO_LETTER_DEGREES
)

# Ordered (regex, canonical label) pairs for recognized certifications.
_CERT_PATTERNS = (
    (r"AWS Certified [A-Za-z][\w -]{2,40}", "AWS Certified"),
    (r"Certified Kubernetes Administrator", "Certified Kubernetes Administrator"),
    (r"Certified Kubernetes Application Developer", "Certified Kubernetes Application Developer"),
    (r"Google Cloud (?:Certified )?Professional [A-Za-z][\w ]{2,40}", "Google Cloud Professional"),
    (r"Microsoft (?:Azure )?Certified[\w -]{2,40}", "Microsoft Certified"),
    (r"Azure (?:Administrator|Solutions Architect|Developer|Security Engineer)(?: Associate| Expert)?",
     "Azure Certified"),
    (r"Oracle Certified Professional", "Oracle Certified Professional"),
    (r"Salesforce Certified[\w -]{2,40}", "Salesforce Certified"),
    (r"Certified Scrum (?:Master|Product Owner|Developer)", "Certified Scrum"),
    (r"(?:Certified )?Scrum Master", "Scrum Master"),
    (r"CompTIA (?:Security\+|Network\+|A\+|Cloud\+)", "CompTIA"),
    (r"(?:Security\+|Network\+|Cloud\+)\b", None),  # bare cert suffixes
    (r"Lean Six Sigma(?: Black| Green)? Belt", "Lean Six Sigma"),
    (r"Six Sigma(?: Black| Green)? Belt", "Six Sigma"),
    (r"ITIL(?: \d| Foundation)?\b", "ITIL"),
    (r"PMP\b", "PMP"),
    (r"CISSP\b", "CISSP"),
    (r"CCNA\b", "CCNA"),
    (r"CCNP\b", "CCNP"),
    (r"CCIE\b", "CCIE"),
    (r"CEH\b", "CEH"),
    (r"CISM\b", "CISM"),
    (r"CISA\b", "CISA"),
    (r"CFA\b", "CFA"),
    (r"CPA\b", "CPA"),
    (r"CMA\b", "CMA"),
    (r"Tableau Desktop Specialist", "Tableau Desktop Specialist"),
)

_CERT_RES = [
    (re.compile(pattern, re.IGNORECASE), label)
    for pattern, label in _CERT_PATTERNS
]

# Role keywords, longest-first so "Full Stack Developer" wins over "Developer".
_ROLE_TERMS = (
    "Machine Learning Engineer", "Deep Learning Engineer", "Data Scientist",
    "Data Engineer", "Data Analyst", "ML Engineer", "DevOps Engineer",
    "Cloud Engineer", "Security Engineer", "Network Engineer", "QA Engineer",
    "Test Engineer", "Backend Engineer", "Backend Developer",
    "Frontend Engineer", "Frontend Developer", "Full Stack Engineer",
    "Full Stack Developer", "Software Engineer", "Software Developer",
    "Software Architect", "Solutions Architect", "Engineering Manager",
    "Product Manager", "Project Manager", "Program Manager", "Technical Lead",
    "Team Lead", "Business Analyst", "Financial Analyst", "Research Assistant",
    "Teaching Assistant", "Database Administrator", "UX Designer",
    "UI Designer", "Graphic Designer", "Marketing Manager", "Consultant",
    "Engineer", "Developer", "Designer", "Architect", "Analyst", "Scientist",
    "Manager", "Director", "Coordinator", "Specialist", "Administrator",
    "Researcher", "SRE", "DBA",
)

_SENIORITY = (
    "senior", "junior", "lead", "principal", "staff", "head", "chief",
    "executive", "associate", "mid-level", "mid level",
)

# A title match must be a whole word at both edges so "Engineer" cannot fire
# inside "engineers" or "engineered".
_TITLE_RE = re.compile(
    r"(?<![A-Za-z])(?:(?:%s)\s+)?(?:%s)(?![A-Za-z])"
    % (
        "|".join(sorted(_SENIORITY, key=len, reverse=True)),
        "|".join(sorted(_ROLE_TERMS, key=len, reverse=True)),
    ),
    re.IGNORECASE,
)

_YEARS_EXPERIENCE_RES = (
    # "5+ years of experience", "5 years experience"
    re.compile(
        r"(?<![\d.])(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience",
        re.IGNORECASE,
    ),
    # "5 to 7 years"
    re.compile(
        r"(?<![\d.])(\d{1,2})\s*(?:-|–|to)\s*(\d{1,2})\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
    # "over 5 years", "more than 5 years"
    re.compile(
        r"(?:over|more than)\s+(\d{1,2})\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
)

_COMPANY_SUFFIX_RE = re.compile(
    r"\b[A-Z][A-Za-z0-9&.]{1,40}\s+(?:Inc\.?|LLC|Ltd\.?|Limited|GmbH|"
    r"Corp(?:oration)?\.?|Pvt\.?|Technologies?|Systems?|Labs?|Group|"
    r"Consulting|Analytics)\b"
)

# Common "wanted-skill" words that would false-positive as degree/cert keywords.
_WANTED_SKILL_WORDS = {
    "professional", "summary", "objective", "profile", "skills", "experience",
    "education", "projects", "certifications", "languages", "awards",
    "interests", "references", "contact",
}


def _dedup(items):
    """De-duplicate while preserving order."""
    seen = set()
    out = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def extract_degrees(text):
    """Return canonical degree labels present in the text."""
    if not text:
        return []

    found = []
    for pattern, label in _DEGREE_RES:
        if pattern.search(text):
            found.append(label)

    return _dedup(found)


def extract_certifications(text):
    """Return canonical certification labels present in the text."""
    if not text:
        return []

    found = []
    for pattern, label in _CERT_RES:
        match = pattern.search(text)
        if not match:
            continue
        found.append(label or match.group(0))

    return _dedup(found)


def extract_job_titles(text):
    """Return de-duplicated job titles found in the text."""
    if not text:
        return []

    titles = []
    for match in _TITLE_RE.finditer(text):
        raw = match.group(0).strip()
        if not raw:
            continue
        # Skip when the match is only a bare generic term like "Manager"
        # used as a section header keyword.
        low = raw.lower()
        if low in _WANTED_SKILL_WORDS or low.split()[0] in _WANTED_SKILL_WORDS:
            continue
        titles.append(_title_case(raw))

    return _dedup(titles)


def _title_case(phrase):
    """Title-case words but keep well-known acronyms uppercase."""
    acronyms = {"SRE", "DBA", "QA", "UX", "UI", "ML", "AI", "AWS", "PMP"}
    parts = []
    for word in phrase.split():
        if word.upper() in acronyms:
            parts.append(word.upper())
        else:
            parts.append(word.capitalize())
    return " ".join(parts)


def extract_companies(text):
    """Return company names via spaCy ORG entities plus a suffix rule."""
    if not text:
        return []

    found = []

    nlp = _get_nlp()
    if nlp is not None:
        doc = nlp(text[:20000])  # NER on very long resumes is slow; cap input.
        for ent in doc.ents:
            if ent.label_ != "ORG":
                continue
            # Drop multi-line spans and skill words that spaCy mislabels as ORG.
            if "\n" in ent.text:
                continue
            if ent.text.lower().strip() in _SKILL_NAME_LOOKUP:
                continue
            found.append(ent.text)

    for match in _COMPANY_SUFFIX_RE.finditer(text):
        found.append(match.group(0).strip())

    return _dedup(found)


def extract_years_of_experience(text):
    """Return the maximum explicitly-stated years of experience, or None."""
    if not text:
        return None

    candidates = []

    for pattern in _YEARS_EXPERIENCE_RES:
        for match in pattern.finditer(text):
            groups = [g for g in match.groups() if g]
            if groups:
                candidates.append(int(max(groups, key=int)))

    return max(candidates) if candidates else None


def extract_entities(text):
    """
    High-level extraction used by the analyzer.

    Returns:
        {
            "degrees": [...],
            "certifications": [...],
            "job_titles": [...],
            "companies": [...],
            "years_of_experience": int | None,
        }
    """
    if not text:
        return {
            "degrees": [],
            "certifications": [],
            "job_titles": [],
            "companies": [],
            "years_of_experience": None,
        }

    # Job titles are most meaningful inside the experience section.
    experience = get_section(text, "experience")

    return {
        "degrees": extract_degrees(text),
        "certifications": extract_certifications(text),
        "job_titles": extract_job_titles(experience or text),
        "companies": extract_companies(text),
        "years_of_experience": extract_years_of_experience(text),
    }