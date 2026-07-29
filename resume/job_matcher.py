\
import re
from .skills import SKILLS


def extract_job_skills(job_description: str):
    """
    Extract known skills from the job description.
    """
    text = (job_description or "").lower()
    found = []

    for skill in SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text):
            found.append(skill.title())

    return sorted(set(found))


def calculate_job_fit(resume_skills, job_description: str):
    """
    Returns:
    {
        job_fit_score,
        matching_skills,
        missing_skills,
        extra_skills,
        recommendations
    }
    """

    resume_set = {s.lower() for s in resume_skills}
    job_skills = extract_job_skills(job_description)
    job_set = {s.lower() for s in job_skills}

    if not job_set:
        return {
            "job_fit_score": None,
            "matching_skills": [],
            "missing_skills": [],
            "extra_skills": sorted([s.title() for s in resume_set]),
            "recommendations": [
                "No job description provided."
            ]
        }

    matching = sorted(job_set & resume_set)
    missing = sorted(job_set - resume_set)
    extra = sorted(resume_set - job_set)

    score = round((len(matching) / len(job_set)) * 100)

    recommendations = []

    for skill in missing:
        recommendations.append(
            f"Consider adding or highlighting {skill.title()} experience if applicable."
        )

    if score >= 90:
        recommendations.insert(0, "Excellent match for this job.")
    elif score >= 75:
        recommendations.insert(0, "Good match. Minor improvements can increase your chances.")
    elif score >= 50:
        recommendations.insert(0, "Moderate match. Add the missing skills where appropriate.")
    else:
        recommendations.insert(0, "Low match. Tailor your resume to this job description.")

    return {
        "job_fit_score": score,
        "matching_skills": [s.title() for s in matching],
        "missing_skills": [s.title() for s in missing],
        "extra_skills": [s.title() for s in extra],
        "recommendations": recommendations,
    }
