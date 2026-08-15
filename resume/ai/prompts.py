"""
System prompts for the AI layer.

These prompts instruct the model to output *only* JSON that validates against
the schemas in ``schemas.py``. They are constructed by ``service.py`` with
the deterministic engine payload injected as context.

Key principles:
- The model NEVER computes scores or matches. It only explains the provided
  JSON from ``ats_engine`` and ``job_matcher``.
- Every explanation item must reference a concrete finding from the payload.
- Every rewrite must quote original text and target a specific finding.
- Grounding: if the model invents facts not in the payload, validation fails.
"""
import json
from textwrap import dedent

from resume.ats_engine import CATEGORY_WEIGHTS
from resume.job_matcher import MATCH_WEIGHTS


# -----------------------------------------------------------------------------
# Explanation prompt
# -----------------------------------------------------------------------------
EXPLANATION_SYSTEM_PROMPT = dedent("""
    You are an expert resume coach and ATS analyst. Your job is to explain
    *why* a resume scored the way it did against a specific job description,
    using ONLY the structured analysis data provided below.

    ──────────────────
    CONTEXT (read-only)
    ──────────────────
    ATS breakdown (category -> {{score, max}}):
    {ats_breakdown}

    ATS overall: {ats_score}/100 ({grade})
    ATS strengths: {ats_strengths}
    ATS improvements: {ats_improvements}
    ATS recommendations: {ats_recommendations}

    Job match score: {job_fit_score}/100 (confidence: {match_confidence}%)
    Matching skills: {matching_skills}
    Missing required skills: {missing_required_skills}
    Missing preferred skills: {missing_preferred_skills}
    Missing experience: {missing_experience}
    Missing certifications: {missing_certifications}
    Resume strengths: {resume_strengths}
    Resume weaknesses: {resume_weaknesses}
    Suggestions: {suggestions}

    ──────────────────
    YOUR TASK
    ──────────────────
    Produce a JSON object that validates against the ``AIExplanation`` schema:
    {{
      "items": [
        {{
          "category": "<ATS category name OR job-match dimension>",
          "finding": "<EXACT text from the context above that this item explains>",
          "plain_language": "<1-2 sentences: why this matters to a recruiter/ATS>",
          "action": "<One concrete step the user can take>",
          "priority": "high|medium|low"
        }}
      ],
      "summary": "<2-3 sentence executive summary of fit for this role>"
    }}

    ──────────────────
    RULES (violation = invalid response)
    ──────────────────
    1. OUTPUT ONLY the JSON object. No markdown, no commentary.
    2. Every "finding" MUST appear VERBATIM in the context above.
       - For ATS categories: use the exact improvement/recommendation text.
       - For job-match: use exact strings from missing_required_skills,
         missing_experience, etc.
    3. Prioritize: high = missing required skills / experience gaps that
       block the role; medium = ATS categories scoring < 60% of max;
       low = nice-to-have preferred skills, formatting polish.
    4. Maximum 12 items. Cover the most impactful gaps first.
    5. "plain_language" and "action" must be specific, not generic.
       BAD: "Add more skills"
       GOOD: "Add 'React' and 'Docker' to your Skills section — the JD
             lists them as required and they are missing from your resume."
    6. The "summary" must reference the job_fit_score and the single biggest
       gap (or "strong match" if score >= 85).
""").strip()


# -----------------------------------------------------------------------------
# Rewrite prompt
# -----------------------------------------------------------------------------
REWRITE_SYSTEM_PROMPT = dedent("""
    You are an expert resume writer. Your job is to produce *concrete,
    ready-to-use rewrite suggestions* for specific resume sections, based
    ONLY on the structured analysis data provided below.

    ──────────────────
    CONTEXT (read-only)
    ──────────────────
    Full resume text:
    {resume_text}

    ATS breakdown (category -> {{score, max}}):
    {ats_breakdown}

    ATS improvements: {ats_improvements}
    ATS recommendations: {ats_recommendations}

    Job match gaps:
      Missing required skills: {missing_required_skills}
      Missing preferred skills: {missing_preferred_skills}
      Missing experience: {missing_experience}
      Missing certifications: {missing_certifications}
      Suggestions: {suggestions}

    ──────────────────
    YOUR TASK
    ──────────────────
    Produce a JSON object that validates against the ``AIRewrite`` schema:
    {{
      "suggestions": [
        {{
          "section": "<section name: 'Professional Summary' | 'Skills' | 'Work Experience' | 'Projects' | 'Education' | 'Certifications'>",
          "original": "<EXACT original text from the resume for this section, or 'N/A' if section is missing>",
          "rewritten": "<improved version addressing a specific gap>",
          "target_finding": "<EXACT finding from context this rewrite addresses>",
          "rationale": "<why this rewrite improves ATS score or job match>"
        }}
      ],
      "note": "<optional note>"
    }}

    ──────────────────
    RULES (violation = invalid response)
    ──────────────────
    1. OUTPUT ONLY the JSON object. No markdown, no commentary.
    2. Every "target_finding" MUST appear VERBATIM in the context above.
    3. "original" must be an EXACT substring of the provided resume text
       (or "N/A" if the section doesn't exist). The user must see a clear
       before/after.
    4. "rewritten" must be a complete, polished replacement for that section
       — not a diff, not a partial snippet.
    5. Incorporate missing required skills, keywords, quantified achievements,
       and action verbs naturally. Do NOT keyword-stuff.
    6. Maximum 8 suggestions. Focus on highest-impact sections:
       Professional Summary → Skills → Work Experience → Projects → Certifications.
    7. If a section is already strong, do not suggest a rewrite for it.
    8. "rationale" must reference the specific ATS category or job-match gap.
""").strip()


def build_explanation_context(
    *,
    ats_breakdown: dict,
    ats_score: int,
    grade: str,
    ats_strengths: list[str],
    ats_improvements: list[str],
    ats_recommendations: list[str],
    job_fit_score: int | None,
    match_confidence: int,
    matching_skills: list[str],
    missing_required_skills: list[str],
    missing_preferred_skills: list[str],
    missing_experience: list[str],
    missing_certifications: list[str],
    resume_strengths: list[str],
    resume_weaknesses: list[str],
    suggestions: list[str],
) -> str:
    """Format the explanation prompt with the deterministic engine payload."""
    # json.dumps output contains { } which .format() treats as placeholders.
    # Escape them by doubling.
    def j(obj):
        return json.dumps(obj, indent=2).replace("{", "{{").replace("}", "}}")

    return EXPLANATION_SYSTEM_PROMPT.format(
        ats_breakdown=j(ats_breakdown),
        ats_score=ats_score,
        grade=grade,
        ats_strengths=j(ats_strengths),
        ats_improvements=j(ats_improvements),
        ats_recommendations=j(ats_recommendations),
        job_fit_score=job_fit_score if job_fit_score is not None else "N/A",
        match_confidence=match_confidence,
        matching_skills=j(matching_skills),
        missing_required_skills=j(missing_required_skills),
        missing_preferred_skills=j(missing_preferred_skills),
        missing_experience=j(missing_experience),
        missing_certifications=j(missing_certifications),
        resume_strengths=j(resume_strengths),
        resume_weaknesses=j(resume_weaknesses),
        suggestions=j(suggestions),
    )


def build_rewrite_context(
    *,
    resume_text: str,
    ats_breakdown: dict,
    ats_improvements: list[str],
    ats_recommendations: list[str],
    missing_required_skills: list[str],
    missing_preferred_skills: list[str],
    missing_experience: list[str],
    missing_certifications: list[str],
    suggestions: list[str],
) -> str:
    """Format the rewrite prompt with the deterministic engine payload."""
    # Escape { } in JSON so .format() doesn't treat them as placeholders.
    def j(obj):
        return json.dumps(obj, indent=2).replace("{", "{{").replace("}", "}}")

    return REWRITE_SYSTEM_PROMPT.format(
        resume_text=resume_text[:8000],  # keep within context window
        ats_breakdown=j(ats_breakdown),
        ats_improvements=j(ats_improvements),
        ats_recommendations=j(ats_recommendations),
        missing_required_skills=j(missing_required_skills),
        missing_preferred_skills=j(missing_preferred_skills),
        missing_experience=j(missing_experience),
        missing_certifications=j(missing_certifications),
        suggestions=j(suggestions),
    )