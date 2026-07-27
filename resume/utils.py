import pdfplumber
import re

SKILLS = [
    "python", "java", "c", "c++", "c#", "javascript",
    "typescript", "php", "go", "rust", "kotlin",
    "swift", "r", "matlab",
    "html", "css", "bootstrap", "tailwind",
    "react", "angular", "vue", "jquery",
    "django", "flask", "fastapi",
    "spring", "spring boot",
    "laravel", "nodejs", "express",
    "mysql", "postgresql", "mongodb",
    "sqlite", "oracle", "firebase",
    "aws", "azure", "gcp",
    "docker", "kubernetes",
    "linux", "git", "github",
    "tensorflow", "pytorch",
    "opencv", "numpy",
    "pandas", "scikit-learn",
    "rest api", "graphql",
    "figma", "postman",
    "jira"
]


def extract_text(pdf_path):

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

    return text


def detect_skills(text):

    text = text.lower()

    found = []
    missing = []

    for skill in SKILLS:

        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, text):

            found.append(skill.title())

        else:

            missing.append(skill.title())

    return sorted(set(found)), sorted(set(missing))


def calculate_ats_score(text):

    text_lower = text.lower()

    score = 0

    breakdown = {}

    recommendations = []

    # Name (simple check)
    if len(text.split()) > 5:
        score += 5
        breakdown["Contact"] = 5
    else:
        breakdown["Contact"] = 0
        recommendations.append("Add your full name at the top of the resume.")

    # Email
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        score += 5
        breakdown["Email"] = 5
    else:
        breakdown["Email"] = 0
        recommendations.append("Add a professional email address.")

    # Phone
    if re.search(r"\+?\d[\d\s\-]{8,15}", text):
        score += 5
        breakdown["Phone"] = 5
    else:
        breakdown["Phone"] = 0
        recommendations.append("Add a phone number.")

    # Summary
    if "summary" in text_lower or "profile" in text_lower:
        score += 10
        breakdown["Summary"] = 10
    else:
        breakdown["Summary"] = 0
        recommendations.append("Add a professional summary section.")

    # Skills
    found, _ = detect_skills(text)

    skill_score = min(len(found), 10)

    skill_score *= 2

    score += skill_score

    breakdown["Skills"] = skill_score

    if skill_score < 10:
        recommendations.append("Include more relevant technical skills.")

    # Experience
    if "experience" in text_lower:

        score += 20

        breakdown["Experience"] = 20

    else:

        breakdown["Experience"] = 0

        recommendations.append("Include work experience or internships.")

    # Education
    if "education" in text_lower:

        score += 15

        breakdown["Education"] = 15

    else:

        breakdown["Education"] = 0

        recommendations.append("Add an education section.")

    # Projects
    if "project" in text_lower:

        score += 15

        breakdown["Projects"] = 15

    else:

        breakdown["Projects"] = 0

        recommendations.append("Include academic or personal projects.")

    # Resume Length
    words = len(text.split())

    if 250 <= words <= 1000:

        score += 10

        breakdown["Length"] = 10

    else:

        breakdown["Length"] = 0

        recommendations.append("Aim for 250–1000 words.")

    # Formatting
    if len(text.strip()) > 100:

        score += 15

        breakdown["Formatting"] = 15

    else:

        breakdown["Formatting"] = 0

        recommendations.append("Resume content appears too short.")

    return score, breakdown, recommendations