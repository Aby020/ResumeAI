import re

from .nlp.skill_extractor import canonical_skills
from .skills import COMMON_SKILLS
from .text_extractor import extract_text


def detect_skills(text):
    """
    Detect technical skills from resume text.

    Returns:
        found_skills: canonical skill names found in the text
        missing_skills: a short list of common in-demand skills NOT found
                        (capped so the suggestion list stays readable)
    """

    found = canonical_skills(text)

    found_set = set(found)

    missing = [
        skill for skill in COMMON_SKILLS if skill not in found_set
    ]

    return (
        found,
        missing[:12]
    )


def normalize_text(text):
    """
    Basic text cleanup.
    """

    if not text:
        return ""

    text = text.replace("\n", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def count_words(text):

    return len(
        normalize_text(text).split()
    )


def count_characters(text):

    return len(
        normalize_text(text)
    )


def has_email(text):

    return re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    ) is not None


def has_phone(text):

    return re.search(
        r"\+?\d[\d\s\-]{8,15}",
        text
    ) is not None


def has_linkedin(text):

    return "linkedin.com" in text.lower()


def has_github(text):

    return "github.com" in text.lower()


def resume_statistics(text):
    """
    Statistics shown in dashboard.
    """

    return {

        "word_count": count_words(text),

        "character_count": count_characters(text),

        "has_email": has_email(text),

        "has_phone": has_phone(text),

        "has_linkedin": has_linkedin(text),

        "has_github": has_github(text)

    }


__all__ = [

    "extract_text",

    "detect_skills",

    "normalize_text",

    "count_words",

    "count_characters",

    "resume_statistics",

    "has_email",

    "has_phone",

    "has_linkedin",

    "has_github"

]