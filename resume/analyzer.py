"""
Single-pass resume analysis pipeline.

Builds a structured `ResumeDocument` from raw resume text in one pass so the
ATS scorer, job matcher and dashboard statistics all consume the same parsed
view instead of re-scanning the text independently.
"""
from dataclasses import dataclass, field

from .nlp.entities import extract_entities
from .nlp.features import (
    consistent_dates,
    count_action_verbs,
    count_bullets,
    count_quantified_achievements,
    extract_date_ranges,
    extract_years_worked,
)
from .nlp.sections import SECTION_KINDS, detect_sections, section_coverage
from .nlp.skill_extractor import canonical_skills, extract_skills
from .utils import (
    count_characters,
    count_words,
    has_email,
    has_github,
    has_linkedin,
    has_phone,
)


@dataclass
class ResumeDocument:
    """Structured, analysis-ready view of a resume."""

    text: str
    word_count: int = 0
    character_count: int = 0
    is_scanned: bool = False
    page_count: int = 0

    sections: list = field(default_factory=list)  # ordered {kind, header, content}
    coverage: dict = field(default_factory=dict)  # kind -> present bool
    skills: list = field(default_factory=list)    # {name, category, weight, count}
    canonical_skills: list = field(default_factory=list)
    entities: dict = field(default_factory=dict)  # degrees/certs/titles/companies/years
    features: dict = field(default_factory=dict)  # action verbs/bullets/quantified/dates

    has_email: bool = False
    has_phone: bool = False
    has_linkedin: bool = False
    has_github: bool = False

    # ------------------------------------------------------------------
    def to_dict(self):
        """Serializable dict for persisting into the resume_json field."""
        return {
            "word_count": self.word_count,
            "character_count": self.character_count,
            "is_scanned": self.is_scanned,
            "page_count": self.page_count,
            "sections": self.sections,
            "coverage": self.coverage,
            "skills": self.skills,
            "canonical_skills": self.canonical_skills,
            "entities": self.entities,
            "features": self.features,
            "has_email": self.has_email,
            "has_phone": self.has_phone,
            "has_linkedin": self.has_linkedin,
            "has_github": self.has_github,
        }


def analyze(text, is_scanned=False, page_count=0):
    """Build a ResumeDocument from raw resume text in a single pass."""
    text = text or ""

    doc = ResumeDocument(
        text=text,
        is_scanned=bool(is_scanned),
        page_count=page_count,
    )

    # Basic statistics
    doc.word_count = count_words(text)
    doc.character_count = count_characters(text)

    # Sections & coverage
    doc.sections = detect_sections(text)
    doc.coverage = section_coverage(text)

    # Skills (canonical, alias-resolved)
    doc.skills = extract_skills(text)
    doc.canonical_skills = canonical_skills(text)

    # Entities (degrees, certifications, titles, companies, years)
    doc.entities = extract_entities(text)

    # Language / structure features
    doc.features = {
        "action_verb_count": count_action_verbs(text),
        "bullet_count": count_bullets(text),
        "quantified_achievements": count_quantified_achievements(text),
        "date_ranges": extract_date_ranges(text),
        "years_worked": extract_years_worked(text),
        "consistent_dates": consistent_dates(text),
    }

    # Contact signals
    doc.has_email = has_email(text)
    doc.has_phone = has_phone(text)
    doc.has_linkedin = has_linkedin(text)
    doc.has_github = has_github(text)

    return doc


__all__ = ["ResumeDocument", "analyze", "SECTION_KINDS"]