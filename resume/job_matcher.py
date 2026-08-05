"""
Weighted job-matching engine.

Compares a candidate's structured `ResumeDocument` (Phase 2) against the
requirements extracted from a job description across six weighted dimensions:
skills (required vs preferred), experience, education, certifications, job
title similarity, and domain/responsibility vocabulary. Matching runs on
canonicalized terms, so JS == JavaScript, ML == Machine Learning and
React.js == React.

The public contract of `calculate_job_fit` is preserved:
    {
        job_fit_score,            # 0-100, or None when no JD skills exist
        matching_skills,
        missing_skills,
        extra_skills,
        recommendations,          # actionable, prioritized suggestions
    }
plus a richer set of new keys (match_confidence, strong_matches,
missing_required_skills, missing_preferred_skills, missing_experience,
missing_certifications, missing_technologies, resume_strengths,
resume_weaknesses, suggestions).

All weights live in MATCH_WEIGHTS so future tuning is a config change, not
logic change.
"""
import re

from .nlp.entities import (
    extract_certifications,
    extract_degrees,
    extract_job_titles,
)
from .nlp.normalize import lemmatize, redact_contact, tokenize
from .nlp.skill_extractor import canonical_skills
from .skills import SKILL_CATEGORY_OF

# ---------------------------------------------------------------------------
# Configuration — the single place to tune matching behaviour.
# ---------------------------------------------------------------------------
MATCH_WEIGHTS = {
    "skills": 45,           # canonical overlap, required weighted over preferred
    "experience": 20,       # years required by JD vs years shown on resume
    "education": 10,        # JD degree requirement vs highest resume degree
    "certifications": 5,    # JD-listed certs vs resume certs
    "title": 5,             # JD role vs resume job titles
    "domain": 15,           # responsibility / industry keyword coverage
}

TOTAL_MAX = sum(MATCH_WEIGHTS.values())  # 100

# Degree ladder used to compare "JD asks for X" with "resume has Y".
_DEGREE_LADDER = {
    "PhD": 5,
    "Doctorate": 5,
    "M.Phil": 4,
    "Master's": 4,
    "MBA": 4,
    "M.Tech": 4,
    "M.E": 4,
    "M.S": 4,
    "M.A": 4,
    "M.Sc": 4,
    "M.Com": 4,
    "Bachelor's": 3,
    "B.Tech": 3,
    "B.E": 3,
    "B.S": 3,
    "B.A": 3,
    "B.Sc": 3,
    "B.Com": 3,
    "BBA": 3,
    "Associate's": 2,
}

_REQUIRED_MARKERS = re.compile(
    r"\b(?:required|requirements?|must have|must-have|essential|minimum|"
    r"mandatory|qualifications?|you (?:will|should|must) have|"
    r"what you.?ll need)\b",
    re.IGNORECASE,
)

_PREFERRED_MARKERS = re.compile(
    r"\b(?:preferred|preference|nice to have|nice-to-have|good to have|"
    r"bonus|plus|desirable|desired|would be a plus)\b",
    re.IGNORECASE,
)

_YEARS_RES = (
    # "5+ years of experience", "5 years experience in Python"
    re.compile(r"(?<![\d.])(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience", re.I),
    # "5+ years required / needed / minimum"
    re.compile(r"(?<![\d.])(\d{1,2})\+?\s*(?:years?|yrs?)\s+(?:required|needed|minimum)", re.I),
    # "minimum / at least 5 years"
    re.compile(r"(?:minimum|at least)\s+(\d{1,2})\s*(?:years?|yrs?)", re.I),
)

_STOPWORDS = {
    "about", "ability", "able", "across", "after", "also", "among", "and",
    "are", "based", "been", "being", "beyond", "both", "business", "can",
    "company", "context", "current", "data", "during", "each", "etc", "from",
    "good", "great", "group", "have", "having", "highly", "including", "into",
    "job", "knowledge", "lead", "level", "make", "may", "must", "need",
    "needs", "new", "other", "our", "over", "prior", "provide", "related",
    "relevant", "role", "skills", "strong", "support", "team", "their",
    "them", "these", "they", "this", "through", "using", "well", "where",
    "which", "while", "will", "with", "within", "work", "working", "would",
    "years",
}

_SKILL_TOKENS = {
    word.lower()
    for name in SKILL_CATEGORY_OF
    for word in name.split()
    if len(word) >= 2
}

# ---------------------------------------------------------------------------
# JD requirement extraction
# ---------------------------------------------------------------------------

def extract_job_skills(job_description):
    """
    Extract canonical skills mentioned in the job description.

    Aliases are resolved before matching, so a job description asking for "JS"
    is equivalent to one asking for "JavaScript".
    """
    return canonical_skills(job_description or "")


def extract_job_years(job_description):
    """Return the highest years-of-experience figure demanded by the JD."""
    if not job_description:
        return None

    values = []
    for pattern in _YEARS_RES:
        for match in pattern.finditer(job_description):
            values.append(int(match.group(1)))

    return max(values) if values else None


def _classify_skill(job_description, skill):
    """
    Classify a job skill as "required" or "preferred" by scanning the text
    window around its occurrences for marker words.

    "Required" wins: if a skill appears anywhere near a required marker it is
    required, even if it is also listed under a preferred/plus section.
    """
    pattern = re.compile(
        r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(skill),
        re.IGNORECASE,
    )

    occurrences = list(pattern.finditer(job_description))
    if not occurrences:
        return "required"

    for marker, label in ((_REQUIRED_MARKERS, "required"),
                          (_PREFERRED_MARKERS, "preferred")):
        for match in occurrences:
            window = job_description[
                max(0, match.start() - 80): match.end() + 40
            ]
            if marker.search(window):
                return label

    return "required"


def extract_job_requirements(job_description):
    """
    Extract a structured view of the job description.

    Returns:
        {
            "required_skills": [...],   # canonical
            "preferred_skills": [...],  # canonical
            "years": int | None,        # years of experience demanded
            "degrees": [...],           # canonical degree labels
            "certifications": [...],    # canonical cert labels
            "title": str,               # best-effort job title
        }
    """
    if not job_description:
        return {
            "required_skills": [],
            "preferred_skills": [],
            "years": None,
            "degrees": [],
            "certifications": [],
            "title": "",
        }

    required, preferred = [], []
    for skill in canonical_skills(job_description):
        if _classify_skill(job_description, skill) == "preferred":
            preferred.append(skill)
        else:
            required.append(skill)

    return {
        "required_skills": required,
        "preferred_skills": preferred,
        "years": extract_job_years(job_description),
        "degrees": extract_degrees(job_description),
        "certifications": extract_certifications(job_description),
        "title": _extract_job_title(job_description),
    }


def _extract_job_title(job_description):
    """Best-effort job title: a role phrase, or the first short heading line."""
    titles = extract_job_titles(job_description)
    if titles:
        return titles[0]

    for line in job_description.splitlines():
        line = line.strip()
        words = line.split()
        if 2 <= len(words) <= 8 and not line.endswith((".", "!", "?")):
            return line

    return ""


# ---------------------------------------------------------------------------
# Similarity helpers
# ---------------------------------------------------------------------------

def _token_similarity(a, b):
    """Jaccard similarity of lemmatized token sets (0.0 .. 1.0)."""
    tokens_a = set(tokenize(lemmatize(a)))
    tokens_b = set(tokenize(lemmatize(b)))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _domain_keywords(text):
    """Meaningful, de-skilled, lemmatized keywords for a piece of text."""
    if not text:
        return set()

    cleaned = redact_contact(text[:20000])
    tokens = set(tokenize(lemmatize(cleaned)))

    return {
        token
        for token in tokens
        if len(token) >= 4
        and token not in _STOPWORDS
        and token not in _SKILL_TOKENS
    }


def _coverage(overlap_count, required_count):
    """0.0 .. 1.0 coverage of a required set."""
    if required_count <= 0:
        return 1.0
    return min(1.0, overlap_count / required_count)


def _fmt_years(value):
    """Render a year count as a clean number (7.0 -> '7', 1.5 -> '1.5')."""
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


# ---------------------------------------------------------------------------
# Dimension scorers — each returns (score, detail)
# ---------------------------------------------------------------------------

def _score_skills(resume_set, requirements):
    weight = MATCH_WEIGHTS["skills"]
    required = requirements["required_skills"]
    preferred = requirements["preferred_skills"]

    if not required and not preferred:
        return None, {}

    matched_required = [s for s in required if s in resume_set]
    matched_preferred = [s for s in preferred if s in resume_set]
    missing_required = [s for s in required if s not in resume_set]
    missing_preferred = [s for s in preferred if s not in resume_set]

    req_ratio = _coverage(len(matched_required), len(required))
    pref_ratio = _coverage(len(matched_preferred), len(preferred))

    score = weight * (0.75 * req_ratio + 0.25 * pref_ratio)

    return score, {
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "missing_required": missing_required,
        "missing_preferred": missing_preferred,
    }


def _score_experience(requirements, resume_years):
    weight = MATCH_WEIGHTS["experience"]
    required_years = requirements["years"]

    if required_years is None:
        return weight, {}  # no constraint stated

    if not resume_years:
        return weight * 0.4, {
            "missing": [f"JD asks for {required_years}+ years of experience; "
                        "resume does not state years of experience."],
        }

    if resume_years >= required_years:
        return weight, {}

    return weight * (resume_years / required_years), {
        "missing": [
            f"JD asks for {required_years}+ years of experience; "
            f"resume shows ~{_fmt_years(resume_years)}."
        ],
    }


def _score_education(requirements, resume_degrees):
    weight = MATCH_WEIGHTS["education"]
    required_level = max(
        (_DEGREE_LADDER.get(d, 0) for d in requirements["degrees"]),
        default=0,
    )

    if not required_level:
        return weight, {}  # no degree requirement

    resume_level = max(
        (_DEGREE_LADDER.get(d, 0) for d in resume_degrees),
        default=0,
    )

    if not resume_level:
        return weight * 0.4, {
            "missing": ["JD requires a degree; resume has no recognized degree."],
        }

    if resume_level >= required_level:
        return weight, {}

    return weight * (resume_level / required_level), {
        "missing": ["JD requires a higher degree level than the resume shows."],
    }


def _score_certifications(requirements, resume_certs):
    weight = MATCH_WEIGHTS["certifications"]
    required_certs = requirements["certifications"]

    if not required_certs:
        return weight, {}  # no certification requirement

    resume_cert_set = set(resume_certs)
    matched = [c for c in required_certs if c in resume_cert_set]
    missing = [c for c in required_certs if c not in resume_cert_set]

    return weight * _coverage(len(matched), len(required_certs)), {
        "matched": matched,
        "missing": missing,
    }


def _score_title(requirements, resume_titles):
    weight = MATCH_WEIGHTS["title"]
    jd_title = requirements["title"]

    if not jd_title:
        return weight, {}  # could not determine the JD role

    if not resume_titles:
        return weight * 0.5, {}

    best = max(_token_similarity(jd_title, t) for t in resume_titles)

    return weight * best, {
        "similarity": best,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_job_fit(resume_skills, job_description, doc=None):
    """
    Weighted composite job-fit scoring.

    Args:
        resume_skills: canonical skill names present on the resume.
        job_description: the raw job description text.
        doc: optional ResumeDocument (Phase 2) used for experience, education,
             certifications, titles and domain vocabulary. When None, those
             dimensions degrade to neutral/unknown.

    Returns:
        job_fit_score, matching_skills, missing_skills, extra_skills,
        recommendations, match_confidence, strong_matches,
        missing_required_skills, missing_preferred_skills, missing_experience,
        missing_certifications, missing_technologies, resume_strengths,
        resume_weaknesses, suggestions
    """
    resume_set = set(resume_skills or [])
    requirements = extract_job_requirements(job_description)

    required = requirements["required_skills"]
    preferred = requirements["preferred_skills"]

    # No usable job description -> preserve the historical "no match" shape.
    if not required and not preferred:
        return {
            "job_fit_score": None,
            "matching_skills": [],
            "missing_skills": [],
            "extra_skills": sorted(resume_set),
            "recommendations": ["No job description provided."],
            "match_confidence": 0,
            "strong_matches": [],
            "missing_required_skills": [],
            "missing_preferred_skills": [],
            "missing_experience": [],
            "missing_certifications": [],
            "missing_technologies": [],
            "resume_strengths": [],
            "resume_weaknesses": [],
            "suggestions": ["Add a job description to see a match score."],
        }

    # Resume-side signals (None when no ResumeDocument was supplied).
    resume_years = None
    resume_degrees = []
    resume_certs = []
    resume_titles = []
    resume_keywords = set()
    if doc is not None:
        resume_years = max(
            doc.entities.get("years_of_experience") or 0,
            doc.features.get("years_worked") or 0,
        ) or None
        resume_degrees = doc.entities.get("degrees") or []
        resume_certs = doc.entities.get("certifications") or []
        resume_titles = doc.entities.get("job_titles") or []
        resume_keywords = _domain_keywords(doc.text)

    # --- Dimension scores -------------------------------------------------
    skills_result, skills_detail = _score_skills(resume_set, requirements)
    exp_score, exp_detail = _score_experience(requirements, resume_years)
    edu_score, edu_detail = _score_education(requirements, resume_degrees)
    cert_score, cert_detail = _score_certifications(requirements, resume_certs)
    title_score, title_detail = _score_title(requirements, resume_titles)

    # Domain/industry coverage: how much of the JD's vocabulary the resume covers.
    jd_keywords = _domain_keywords(job_description)
    overlap = 0
    if not jd_keywords:
        domain_score = MATCH_WEIGHTS["domain"]
    elif not resume_keywords:
        domain_score = MATCH_WEIGHTS["domain"] * 0.5
    else:
        overlap = len(jd_keywords & resume_keywords)
        domain_score = MATCH_WEIGHTS["domain"] * _coverage(overlap, len(jd_keywords))

    # --- Assemble ---------------------------------------------------------
    matching_skills = sorted(
        set(skills_detail["matched_required"]) | set(skills_detail["matched_preferred"])
    )
    missing_required = skills_detail["missing_required"]
    missing_preferred = skills_detail["missing_preferred"]
    missing_all = sorted(set(missing_required) | set(missing_preferred))
    extra_skills = sorted(resume_set - set(required) - set(preferred))
    missing_experience = exp_detail.get("missing", [])
    missing_certifications = cert_detail.get("missing", [])
    missing_technologies = _tech_only(missing_all)

    total = (
        (skills_result or 0)
        + exp_score
        + edu_score
        + cert_score
        + title_score
        + domain_score
    )
    job_fit_score = round(total)

    # Match confidence: fraction of dimensions the JD actually constrained.
    signals = sum(
        [
            bool(required or preferred),
            requirements["years"] is not None,
            bool(requirements["degrees"]),
            bool(requirements["certifications"]),
            bool(requirements["title"]),
            bool(jd_keywords),
        ]
    )
    match_confidence = round(100 * signals / 6)

    # --- Strengths / weaknesses -------------------------------------------
    resume_strengths = [
        f"Strong skill match: {', '.join(matching_skills[:5])}"
        if matching_skills else None,
        f"Meets the {requirements['years']}+ years requirement"
        if (requirements["years"] and resume_years and resume_years >= requirements["years"])
        else None,
        "Experience level satisfies the role"
        if (requirements["years"] and resume_years and resume_years >= requirements["years"])
        else None,
        "Education meets the JD requirement"
        if requirements["degrees"] and _degree_level(resume_degrees) >= _degree_level(requirements["degrees"])
        else None,
        f"Certifications aligned: {', '.join(cert_detail.get('matched', [])[:3])}"
        if cert_detail.get("matched") else None,
        "Job title aligns with the role"
        if title_detail.get("similarity", 0) >= 0.5 else None,
        "Strong domain/industry vocabulary overlap"
        if jd_keywords and overlap >= 0.4 * len(jd_keywords) else None,
    ]
    resume_strengths = [s for s in resume_strengths if s]

    resume_weaknesses = []
    if missing_required:
        resume_weaknesses.append("Missing required skills")
    if missing_experience:
        resume_weaknesses.append("Experience gap vs the JD requirement")
    if missing_certifications:
        resume_weaknesses.append("Missing certifications requested by the JD")
    if requirements["degrees"] and _degree_level(resume_degrees) < _degree_level(requirements["degrees"]):
        resume_weaknesses.append("Education below the JD requirement")

    # --- Strong matches ----------------------------------------------------
    strong_matches = []
    strong_matches.extend(f"Required skill: {s}" for s in skills_detail["matched_required"])
    strong_matches.extend(f"Preferred skill: {s}" for s in skills_detail["matched_preferred"])
    strong_matches.extend(f"Certification: {c}" for c in cert_detail.get("matched", []))
    if requirements["years"] and resume_years and resume_years >= requirements["years"]:
        strong_matches.append(
            f"Experience: {_fmt_years(resume_years)} years "
            f"(JD asked for {requirements['years']}+)"
        )
    if title_detail.get("similarity", 0) >= 0.5 and requirements["title"]:
        strong_matches.append(f"Role alignment: {requirements['title']}")

    # --- Actionable suggestions -------------------------------------------
    suggestions = []
    if missing_required:
        suggestions.append(
            "Add or highlight these required skills: "
            + ", ".join(missing_required[:8])
            + ("..." if len(missing_required) > 8 else "") + "."
        )
    if missing_experience:
        suggestions.extend(missing_experience)
    if requirements["degrees"] and _degree_level(resume_degrees) < _degree_level(requirements["degrees"]):
        suggestions.append("Highlight your education or add a relevant degree.")
    if missing_certifications:
        suggestions.append(
            "Add certifications requested by the JD: "
            + ", ".join(missing_certifications[:4]) + "."
        )
    if missing_preferred:
        suggestions.append(
            "Consider adding preferred skills (bonus points): "
            + ", ".join(missing_preferred[:5]) + "."
        )
    if not suggestions:
        if job_fit_score >= 90:
            suggestions.append("Excellent match for this job.")
        elif job_fit_score >= 75:
            suggestions.append("Good match. Minor improvements can increase your chances.")
        elif job_fit_score >= 50:
            suggestions.append("Moderate match. Tailor your resume to this job description.")
        else:
            suggestions.append("Low match. Tailor your resume to this job description.")

    return {
        "job_fit_score": job_fit_score,
        "matching_skills": matching_skills,
        "missing_skills": missing_all,
        "extra_skills": extra_skills,
        "recommendations": suggestions,
        "match_confidence": match_confidence,
        "strong_matches": strong_matches,
        "missing_required_skills": missing_required,
        "missing_preferred_skills": missing_preferred,
        "missing_experience": missing_experience,
        "missing_certifications": missing_certifications,
        "missing_technologies": missing_technologies,
        "resume_strengths": resume_strengths,
        "resume_weaknesses": resume_weaknesses,
        "suggestions": suggestions,
    }


def _degree_level(degrees):
    """Highest ladder level (0..5) for a list of degree labels."""
    return max((_DEGREE_LADDER.get(d, 0) for d in degrees), default=0)


def _tech_only(skills):
    """Keep only skills that belong to technical (non soft-skill) categories."""
    tech = []
    for skill in skills:
        category = SKILL_CATEGORY_OF.get(skill)
        if category and category != "Soft Skills":
            tech.append(skill)
    return tech