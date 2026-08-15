"""
Pydantic schemas for AI layer input/output validation.

These models define the *structured* contract between the prompt templates
(in ``prompts.py``) and the service layer (``service.py``). The OpenAI
model is instructed to emit JSON that conforms to these shapes. Any response
that fails validation is treated as a provider error and surfaced as
``AIResponseError`` — callers can fall back to the deterministic engine's
raw recommendations without the user seeing a broken UI.

Design notes:
- All string fields are stripped of leading/trailing whitespace.
- ``extra = 'forbid'`` prevents the model from hallucinating extra keys.
- Lists have reasonable max lengths to keep responses bounded.
- ``grounded_in`` fields let the service verify the model didn't invent facts
  that aren't present in the ATS/job-match payload.
"""
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class ExplanationItem(BaseModel):
    """
    One actionable explanation tied to a specific ATS category or job-match gap.

    The model must reference a concrete finding from the deterministic engine
    (e.g. "Skills Relevance: only 2 canonical skills detected" or
    "missing_required_skills: ['React', 'Docker']") rather than making
    generic statements like "improve your skills".
    """
    category: str = Field(
        ...,
        description="ATS category name (e.g. 'Skills Relevance') or job-match dimension "
                    "(e.g. 'missing_required_skills', 'missing_experience')",
    )
    finding: str = Field(
        ...,
        description="Exact finding text from the engine output this item explains",
    )
    plain_language: str = Field(
        ...,
        description="1-2 sentences explaining *why* this matters to a recruiter/ATS",
        min_length=10,
        max_length=500,
    )
    action: str = Field(
        ...,
        description="One concrete step the user can take to address this finding",
        min_length=10,
        max_length=500,
    )
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Urgency: high = blocker for this role, medium = strong signal, low = nice to have",
    )

    @field_validator("category", "finding", "plain_language", "action", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class AIExplanation(BaseModel):
    """
    Full explanation response: a prioritized list of items covering the most
    impactful ATS weaknesses and job-match gaps.

    The service validates that every ``finding`` appears verbatim in the
    engine payload passed to the prompt (grounding check).
    """
    items: list[ExplanationItem] = Field(
        ...,
        min_length=1,
        max_length=12,
        description="Prioritized explanations (high-priority first)",
    )
    summary: str = Field(
        ...,
        description="2-3 sentence executive summary of the resume's fit for this role",
        min_length=20,
        max_length=800,
    )

    @field_validator("summary", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class RewriteSuggestion(BaseModel):
    """
    One concrete rewrite suggestion for a specific resume section.

    The model must quote the *original text* it is rewriting (so the user
    sees a clear before/after) and the *rewritten version* that addresses
    a specific engine finding. ``target_finding`` must match a finding from
    the engine payload.
    """
    section: str = Field(
        ...,
        description="Resume section being rewritten (e.g. 'Professional Summary', 'Work Experience', 'Skills')",
    )
    original: str = Field(
        ...,
        description="Exact original text from the resume (or 'N/A' if adding new content)",
        max_length=2000,
    )
    rewritten: str = Field(
        ...,
        description="Improved version incorporating keywords, metrics, or structure from the engine findings",
        min_length=10,
        max_length=2000,
    )
    target_finding: str = Field(
        ...,
        description="Engine finding this rewrite addresses (must match a finding in the payload)",
    )
    rationale: str = Field(
        ...,
        description="Why this rewrite improves ATS score or job match (1-2 sentences)",
        min_length=10,
        max_length=500,
    )

    @field_validator("section", "original", "rewritten", "target_finding", "rationale", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class AIRewrite(BaseModel):
    """
    Full rewrite response: a list of section-level suggestions.

    The service validates that every ``target_finding`` appears in the
    engine payload (grounding check).
    """
    suggestions: list[RewriteSuggestion] = Field(
        ...,
        min_length=1,
        max_length=8,
        description="Prioritized rewrite suggestions (highest impact first)",
    )
    note: str = Field(
        default="",
        description="Optional note from the model (e.g. 'No rewrite needed for Education')",
        max_length=500,
    )

    @field_validator("note", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }