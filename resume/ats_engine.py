\
import re
from .skills import SKILLS


def _contains(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


def detect_resume_skills(text: str):
    text = text.lower()
    found = []

    for skill in SKILLS:
        if re.search(r"\b" + re.escape(skill.lower()) + r"\b", text):
            found.append(skill)

    return sorted(set(found))


def calculate_ats_score(text: str):
    """
    Returns:
        {
            ats_score,
            grade,
            breakdown,
            strengths,
            improvements,
            recommendations,
            detected_skills
        }
    """
    score = 0
    breakdown = {}
    strengths = []
    improvements = []
    recommendations = []

    # Contact (10)
    contact = 0

    if _contains(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        contact += 5
        strengths.append("Professional email detected")
    else:
        improvements.append("Email missing")
        recommendations.append("Add a professional email address.")

    if _contains(r"\+?\d[\d\s\-]{8,15}", text):
        contact += 5
        strengths.append("Phone number detected")
    else:
        improvements.append("Phone number missing")
        recommendations.append("Add your phone number.")

    breakdown["Contact Information"] = contact
    score += contact

    # Summary (10)
    summary = 10 if _contains(r"\b(summary|profile|objective)\b", text) else 0
    breakdown["Professional Summary"] = summary
    score += summary
    if summary:
        strengths.append("Professional summary available")
    else:
        improvements.append("Summary missing")
        recommendations.append("Add a short professional summary.")

    # Skills (20)
    skills = detect_resume_skills(text)
    skills_score = min(len(skills), 10) * 2
    breakdown["Skills"] = skills_score
    score += skills_score

    if len(skills) >= 8:
        strengths.append("Strong technical skill set")
    else:
        improvements.append("Few technical skills detected")
        recommendations.append("Include more relevant technical skills.")

    # Experience (20)
    exp = 20 if _contains(r"\b(experience|employment|internship|worked)\b", text) else 0
    breakdown["Experience"] = exp
    score += exp

    if exp:
        strengths.append("Experience section found")
    else:
        improvements.append("Experience section missing")
        recommendations.append("Include work experience or internships.")

    # Education (15)
    edu = 15 if _contains(r"\beducation\b", text) else 0
    breakdown["Education"] = edu
    score += edu

    if not edu:
        improvements.append("Education section missing")
        recommendations.append("Add your education details.")

    # Projects (15)
    proj = 15 if _contains(r"\b(project|projects)\b", text) else 0
    breakdown["Projects"] = proj
    score += proj

    if not proj:
        improvements.append("Projects missing")
        recommendations.append("Showcase personal or academic projects.")

    # Length (5)
    words = len(text.split())
    length = 5 if 250 <= words <= 1000 else 0
    breakdown["Resume Length"] = length
    score += length

    if not length:
        recommendations.append("Keep the resume between 250 and 1000 words.")

    # Formatting (5)
    formatting = 5 if len(text.strip()) > 100 else 0
    breakdown["Formatting"] = formatting
    score += formatting

    ats_score = min(score, 100)

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
        "detected_skills": skills,
    }
