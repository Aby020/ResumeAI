"""
Weighted ATS scoring engine.

Replaces the old presence-based checklist (which awarded full marks for merely
containing trigger words like "experience") with a weighted rubric that
evaluates depth per category against the structured `ResumeDocument` built by
the Phase 2 parser. Canonical skills from `nlp.skill_extractor` are used
everywhere, so JS == JavaScript and ML == Machine Learning.

The public contract of `calculate_ats_score` is unchanged:
    {
        ats_score, grade, breakdown, strengths,
        improvements, recommendations, detected_skills
    }

Weights are configurable via CATEGORY_WEIGHTS (a single source of truth that
views import instead of maintaining their own copy).
"""
from .analyzer import analyze
from .nlp.sections import get_section
from .nlp.skill_extractor import canonical_skills

# ---------------------------------------------------------------------------
# Rubric — the single source of truth for category weights (sums to 100).
# ---------------------------------------------------------------------------
CATEGORY_WEIGHTS = {
    "Contact & Links": 5,
    "Sections & Completeness": 10,
    "Professional Summary": 5,
    "Skills Relevance": 25,
    "Experience Quality": 20,
    "Education": 10,
    "Projects & Certifications": 10,
    "Action Verbs & Language": 5,
    "Keyword Density & Context": 5,
    "Formatting & Structure": 5,
}

TOTAL_MAX = sum(CATEGORY_WEIGHTS.values())  # 100

# Level of a degree for the Education category (highest wins).
_DEGREE_LEVEL_SCORE = {
    "PhD": 8,
    "Doctorate": 8,
    "M.Phil": 7,
    "Master's": 6,
    "MBA": 6,
    "M.Tech": 6,
    "M.E": 6,
    "M.S": 6,
    "M.A": 6,
    "M.Sc": 6,
    "M.Com": 6,
    "Bachelor's": 4,
    "B.Tech": 4,
    "B.E": 4,
    "B.S": 4,
    "B.A": 4,
    "B.Sc": 4,
    "B.Com": 4,
    "BBA": 4,
    "Associate's": 2,
}

# Certifications that carry strong signal for recruiters.
_HIGH_VALUE_CERTS = {
    "AWS Certified",
    "Certified Kubernetes Administrator",
    "Certified Kubernetes Application Developer",
    "CISSP",
    "PMP",
    "CCNA",
    "CCNP",
    "CCIE",
    "CEH",
    "Google Cloud Professional",
    "Microsoft Certified",
    "Azure Certified",
    "Oracle Certified Professional",
    "Salesforce Certified",
    "Certified Scrum",
    "Scrum Master",
}

# Tech-focused categories (tools & soft skills don't count toward diversity).
_TECH_CATEGORIES = {
    "Programming Languages",
    "Frontend & Web",
    "Mobile & Cross-Platform",
    "Backend & Frameworks",
    "Databases & Data Stores",
    "Cloud, DevOps & Infrastructure",
    "AI, ML & Data",
}

# Minimum/maximum words a resume should have.
_MIN_WORDS = 250
_MAX_WORDS = 1000

_IDEAL_DENSITY_MIN = 0.01   # skill mentions per word
_IDEAL_DENSITY_MAX = 0.05


def _ratio(score, maximum):
    """0.0 .. 1.0 fraction of the category earned."""
    if maximum <= 0:
        return 0.0
    return score / maximum


def detect_resume_skills(text):
    """
    Return canonical skill names found in the resume text.

    Delegates to the shared canonical extractor so every detector in the
    codebase agrees on one vocabulary (JS == JavaScript, ML == Machine Learning).
    """
    return canonical_skills(text)


def _score_contact(doc):
    """Contact & Links (5): partial credit per channel (integer points)."""
    score = 0
    strengths, improvements, recommendations = [], [], []

    if doc.has_email:
        score += 2
        strengths.append("Professional email detected")
    else:
        improvements.append("Email missing")
        recommendations.append("Add a professional email address.")

    if doc.has_phone:
        score += 1
        strengths.append("Phone number detected")
    else:
        improvements.append("Phone number missing")
        recommendations.append("Add your phone number.")

    if doc.has_linkedin:
        score += 1
        strengths.append("LinkedIn profile included")
    else:
        improvements.append("LinkedIn missing")
        recommendations.append("Add your LinkedIn profile URL.")

    if doc.has_github:
        score += 1
        strengths.append("GitHub/portfolio included")
    else:
        improvements.append("GitHub/portfolio missing")
        recommendations.append("Add a GitHub or portfolio link if you have one.")

    return {
        "score": score,
        "max": CATEGORY_WEIGHTS["Contact & Links"],
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


def _score_sections(doc):
    """Sections & Completeness (10): presence of standard sections."""
    w = {
        "experience": 2.0,
        "education": 2.0,
        "skills": 2.0,
        "summary": 1.5,
        "projects": 1.5,
        "certifications": 0.5,
    }
    score = 0
    present = [kind for kind, ok in doc.coverage.items() if ok]
    for kind, points in w.items():
        if kind in present:
            score += points

    extras = {"languages", "awards", "publications", "volunteering", "interests"}
    if present and any(k in present for k in extras):
        score += 0.5

    score = min(score, CATEGORY_WEIGHTS["Sections & Completeness"])

    strengths, improvements, recommendations = [], [], []
    for kind in ("experience", "education", "skills", "summary"):
        if kind in present:
            strengths.append(f"{kind.capitalize()} section present")
        else:
            improvements.append(f"{kind.capitalize()} section missing")
    if len(present) < 4:
        recommendations.append(
            "Include the standard sections: summary, skills, experience, "
            "education and projects."
        )

    return {
        "score": round(score),
        "max": CATEGORY_WEIGHTS["Sections & Completeness"],
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


def _score_summary(doc):
    """Professional Summary (5): present, well-sized and keyword-bearing."""
    content = get_section(doc.text, "summary") or ""
    score = 0
    strengths, improvements, recommendations = [], [], []

    if content:
        score += 1
        words = len(content.split())
        if 40 <= words <= 200:
            score += 2
            strengths.append("Summary has a good length")
        elif words:
            score += 1
            improvements.append("Summary length is outside the ideal 40-200 words")
            recommendations.append(
                "Keep the professional summary between 40 and 200 words."
            )

        summary_skills = canonical_skills(content)
        if summary_skills:
            score += min(2, len(summary_skills))
            strengths.append("Summary highlights relevant skills")
        else:
            improvements.append("Summary does not mention key skills")
            recommendations.append(
                "Mention 2-3 of your core skills in the summary."
            )
    else:
        improvements.append("Professional summary missing")
        recommendations.append(
            "Add a 3-4 sentence professional summary at the top."
        )

    return {
        "score": round(min(score, CATEGORY_WEIGHTS["Professional Summary"])),
        "max": CATEGORY_WEIGHTS["Professional Summary"],
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


def _score_skills(doc):
    """Skills Relevance (25): canonical count (log-scaled) + category diversity."""
    count = len(doc.skills)
    score = min(20, round(count * 2.5))
    strengths, improvements, recommendations = [], [], []

    categories = {
        s["category"] for s in doc.skills if s["category"] in _TECH_CATEGORIES
    }
    diversity = 0
    if len(categories) >= 3:
        diversity = 5
        strengths.append("Skills span multiple technology areas")
    elif len(categories) == 2:
        diversity = 3
    elif len(categories) == 1:
        diversity = 2

    if count >= 8:
        strengths.append("Strong technical skill set")
    else:
        improvements.append("Few technical skills detected")
        recommendations.append(
            "Include more relevant technical skills across 3+ categories "
            "(languages, frameworks, cloud, data)."
        )

    return {
        "score": round(min(score + diversity, CATEGORY_WEIGHTS["Skills Relevance"])),
        "max": CATEGORY_WEIGHTS["Skills Relevance"],
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


def _score_experience(doc):
    """Experience Quality (20): depth, years, action verbs, impact, titles."""
    max_pts = CATEGORY_WEIGHTS["Experience Quality"]
    score = 0
    strengths, improvements, recommendations = [], [], []

    if doc.coverage.get("experience"):
        score += 3
        strengths.append("Work experience section found")
    else:
        improvements.append("Experience section missing")
        recommendations.append("Include work experience or internships.")

    # Years of experience: explicit statement or inferred from date ranges.
    years = doc.entities.get("years_of_experience") or 0
    years_worked = doc.features.get("years_worked") or 0
    total_years = max(years, years_worked)

    if years:
        score += 3
        strengths.append("Years of experience stated")
    elif doc.coverage.get("experience"):
        score += 1

    if total_years >= 9:
        score += 4
        strengths.append("Substantial years of experience")
    elif total_years >= 5:
        score += 3
        strengths.append("Good years of experience")
    elif total_years >= 2:
        score += 2
    elif total_years:
        score += 1
        improvements.append("Limited years of experience")
        recommendations.append("Emphasize depth over years if your experience is limited.")

    # Action verbs and quantified impact.
    verbs = doc.features.get("action_verb_count", 0)
    quantified = doc.features.get("quantified_achievements", 0)

    score += min(5, verbs)
    if verbs >= 3:
        strengths.append("Strong action verbs used")
    else:
        improvements.append("Few strong action verbs")
        recommendations.append(
            "Start experience bullets with strong action verbs (built, led, optimized)."
        )

    score += min(3, quantified)
    if quantified:
        strengths.append("Quantified achievements included")
    else:
        improvements.append("No quantified achievements")
        recommendations.append(
            "Add metrics to your achievements (%, revenue, users, performance)."
        )

    # Job titles give the scorer concrete context.
    titles = doc.entities.get("job_titles", [])
    score += min(2, len(titles))
    if titles:
        strengths.append("Job titles detected")

    return {
        "score": round(min(score, max_pts)),
        "max": max_pts,
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


def _score_education(doc):
    """Education (10): section presence + highest degree level."""
    max_pts = CATEGORY_WEIGHTS["Education"]
    score = 0
    strengths, improvements, recommendations = [], [], []

    if doc.coverage.get("education"):
        score += 2
        strengths.append("Education section found")
    else:
        improvements.append("Education section missing")
        recommendations.append("Add your education details.")

    degrees = doc.entities.get("degrees", [])
    level = max((_DEGREE_LEVEL_SCORE.get(d, 0) for d in degrees), default=0)
    score += level
    if level >= 6:
        strengths.append("Advanced degree (Master's or higher) recognized")
    elif level >= 4:
        strengths.append("Bachelor's degree recognized")
    elif not degrees:
        improvements.append("No degree recognized")
        recommendations.append(
            "List your degree(s) with the institution and field of study."
        )

    return {
        "score": round(min(score, max_pts)),
        "max": max_pts,
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


def _score_projects_certs(doc):
    """Projects & Certifications (10): projects with tech + certifications."""
    max_pts = CATEGORY_WEIGHTS["Projects & Certifications"]
    score = 0
    strengths, improvements, recommendations = [], [], []

    projects = doc.coverage.get("projects")
    if projects:
        score += 2
        strengths.append("Projects section found")
        project_text = get_section(doc.text, "projects") or ""
        project_skills = canonical_skills(project_text)
        score += min(3, len(project_skills))
        if project_skills:
            strengths.append("Projects showcase technical skills")
        else:
            improvements.append("Projects do not mention technologies used")
            recommendations.append(
                "List the technologies used for each project."
            )
    else:
        improvements.append("Projects section missing")
        recommendations.append("Showcase personal or academic projects.")

    certifications = doc.entities.get("certifications", [])
    if certifications:
        score += 1
        score += min(2, len(certifications))
        if any(c in _HIGH_VALUE_CERTS for c in certifications):
            score += 2
            strengths.append("Recognized professional certifications")
        else:
            score += 1
        strengths.append("Certifications listed")
    else:
        improvements.append("No certifications listed")
        recommendations.append(
            "Add recognized certifications (AWS, PMP, Scrum, etc.)."
        )

    return {
        "score": round(min(score, max_pts)),
        "max": max_pts,
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


def _score_language(doc):
    """Action Verbs & Language (5): verb richness across the resume."""
    verbs = doc.features.get("action_verb_count", 0)
    if verbs >= 6:
        score, strength = 5, "Excellent action-verb usage"
    elif verbs >= 3:
        score, strength = 3, "Good action-verb usage"
    elif verbs >= 1:
        score, strength = 1, "Some action verbs used"
    else:
        score, strength = 0, None

    strengths = [strength] if strength else []
    improvements = [] if verbs >= 1 else [
        "No strong action verbs detected"
    ]
    recommendations = [] if verbs >= 3 else [
        "Use strong action verbs throughout the resume."
    ]

    return {
        "score": score,
        "max": CATEGORY_WEIGHTS["Action Verbs & Language"],
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


def _score_density(doc):
    """
    Keyword Density & Context (5): reward context, penalize stuffing.

    "Stuffing" is modelled as repeating a small set of skills over and over
    (e.g. "Python Python Python ..."). A normal resume lists many distinct
    skills, so the repetition ratio is low and it is not penalized.
    """
    score = 0
    strengths, improvements, recommendations = [], [], []

    skills = doc.skills
    unique = len(skills)
    total_mentions = sum(s["count"] for s in skills)
    repetitions = max(0, total_mentions - unique)  # extra mentions beyond first

    # Balanced vocabulary: an average skill should appear ~1.5x, not 3x+.
    if unique and (repetitions / unique) <= 1.0:
        score += 2
        strengths.append("Well-balanced keyword usage")
    elif unique and (repetitions / unique) <= 2.5:
        score += 1
        improvements.append("Keywords repeated more than necessary")
        recommendations.append("Mention each skill once or twice in context.")
    else:
        improvements.append("Keyword stuffing detected")
        recommendations.append(
            "Remove repeated keywords; write naturally with context."
        )

    # Contextual placement: skills named inside the summary are stronger signal.
    summary = get_section(doc.text, "summary") or ""
    if canonical_skills(summary):
        score += 1
        strengths.append("Skills placed in the summary")

    # No single skill should dominate the resume (count > 4 reads as stuffing).
    if unique and all(s["count"] <= 4 for s in skills):
        score += 1
    else:
        improvements.append("Duplicate keywords detected")

    # Not too sparse: at least ~2% of words should be skill mentions.
    words = doc.word_count
    if unique and words and (total_mentions / words) >= 0.02:
        score += 1
    else:
        improvements.append("Skills are underrepresented in the text")
        recommendations.append("Weave your key skills into bullets and context.")

    return {
        "score": min(score, CATEGORY_WEIGHTS["Keyword Density & Context"]),
        "max": CATEGORY_WEIGHTS["Keyword Density & Context"],
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


def _score_formatting(doc):
    """Formatting & Structure (5): headers, bullets, dates, length."""
    score = 0
    strengths, improvements, recommendations = [], [], []

    header_count = len(doc.sections)
    if header_count >= 3:
        score += 1
        strengths.append("Clear section headers")
    else:
        improvements.append("Few clear section headers")

    if doc.features.get("bullet_count", 0):
        score += 1
        strengths.append("Bullet points used")
    else:
        improvements.append("No bullet points")
        recommendations.append("Use bullet points for readability.")

    if doc.features.get("date_ranges") and doc.features.get("consistent_dates", True):
        score += 1
    elif doc.features.get("date_ranges"):
        improvements.append("Inconsistent date formats")
        recommendations.append("Keep date formats consistent (e.g. Jan 2019 - Present).")

    if _MIN_WORDS <= doc.word_count <= _MAX_WORDS:
        score += 1
        strengths.append("Resume length within ideal range")
    else:
        improvements.append("Resume length outside 250-1000 words")
        recommendations.append("Keep the resume between 250 and 1000 words.")

    if doc.character_count > 300:
        score += 1
    else:
        improvements.append("Resume appears too short")
        recommendations.append("Expand the resume with more detail.")

    return {
        "score": round(min(score, CATEGORY_WEIGHTS["Formatting & Structure"])),
        "max": CATEGORY_WEIGHTS["Formatting & Structure"],
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
    }


# category -> scorer, in a stable display order.
_CATEGORY_SCORERS = (
    ("Contact & Links", _score_contact),
    ("Sections & Completeness", _score_sections),
    ("Professional Summary", _score_summary),
    ("Skills Relevance", _score_skills),
    ("Experience Quality", _score_experience),
    ("Education", _score_education),
    ("Projects & Certifications", _score_projects_certs),
    ("Action Verbs & Language", _score_language),
    ("Keyword Density & Context", _score_density),
    ("Formatting & Structure", _score_formatting),
)


def calculate_ats_score(text: str, doc=None):
    """
    Weighted ATS scoring.

    Args:
        text: raw resume text.
        doc: optional pre-built ResumeDocument (avoids re-parsing when the
             caller already analyzed the text, e.g. for job matching).

    Returns:
        {
            ats_score,
            grade,
            breakdown,        # category -> {"score", "max"}
            strengths,
            improvements,
            recommendations,
            detected_skills  # canonical skill names (for job matching)
        }
    """
    if doc is None:
        doc = analyze(text)

    breakdown = {}
    strengths = []
    improvements = []
    recommendations = []

    for category, scorer in _CATEGORY_SCORERS:
        result = scorer(doc)
        breakdown[category] = {"score": result["score"], "max": result["max"]}
        strengths.extend(result["strengths"])
        improvements.extend(result["improvements"])
        recommendations.extend(result["recommendations"])

    ats_score = min(100, sum(b["score"] for b in breakdown.values()))

    if ats_score >= 90:
        grade = "Excellent"
    elif ats_score >= 75:
        grade = "Good"
    elif ats_score >= 60:
        grade = "Moderate"
    elif ats_score >= 40:
        grade = "Weak"
    else:
        grade = "Poor"

    return {
        "ats_score": ats_score,
        "grade": grade,
        "breakdown": breakdown,
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations,
        "detected_skills": doc.canonical_skills,
    }