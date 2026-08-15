"""
AI Service layer — orchestrates explain/rewrite with caching and grounding.

This is the *only* public entry point for views and tasks. It handles:
- Building prompts from deterministic engine payloads
- Calling the OpenAI client
- Validating responses against pydantic schemas
- Grounding checks (every finding must exist in the engine payload)
- Caching (per resume+JD, versioned)
- Graceful degradation (fallback to raw engine recommendations)
"""
import hashlib
import json
import logging
from functools import lru_cache
from typing import Any

from django.conf import settings
from django.core.cache import cache

from .client import AIResponseError, AIUnavailable, OpenAIClient
from .prompts import build_explanation_context, build_rewrite_context
from .schemas import AIExplanation, AIRewrite, ExplanationItem, RewriteSuggestion

logger = logging.getLogger(__name__)

# Cache key prefix and version. Bump when prompt templates or schemas change.
CACHE_PREFIX = "resume_ai"
CACHE_VERSION = 2
CACHE_TTL = 60 * 60 * 24 * 7  # 7 days


class AIService:
    """
    High-level service for AI-powered resume explanation and rewriting.

    Usage:
        service = AIService()
        explanation = service.explain(ats_payload, job_payload, resume_text)
        rewrites = service.rewrite(ats_payload, job_payload, resume_text)

    Both methods return validated pydantic models (AIExplanation, AIRewrite)
    or None when AI is unavailable/disabled — callers should fall back to
    the deterministic engine's raw recommendations.
    """

    def __init__(self):
        try:
            self._client = OpenAIClient()
            self._enabled = True
        except AIUnavailable as e:
            logger.info("AI service disabled: %s", e)
            self._client = None
            self._enabled = False

        # Development mode: return mock data when AI fails
        self._debug_mode = getattr(settings, "DEBUG_AI", False)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def explain(
        self,
        ats_payload: dict[str, Any],
        job_payload: dict[str, Any],
        resume_text: str,
    ) -> AIExplanation | None:
        """
        Generate a grounded explanation of ATS score and job-match gaps.

        Args:
            ats_payload: Output from ``calculate_ats_score``.
            job_payload: Output from ``calculate_job_fit``.
            resume_text: Raw resume text (for context, not sent to model in explain).

        Returns:
            Validated AIExplanation, or None if AI is unavailable or all
            attempts fail validation.
        """
        if not self._enabled:
            return None

        cache_key = self._cache_key("explain", ats_payload, job_payload)
        cached = cache.get(cache_key)
        if cached:
            try:
                return AIExplanation.model_validate(cached)
            except Exception:
                logger.debug("Cached explanation failed validation, recomputing")

        prompt = build_explanation_context(
            ats_breakdown=ats_payload["breakdown"],
            ats_score=ats_payload["ats_score"],
            grade=ats_payload["grade"],
            ats_strengths=ats_payload["strengths"],
            ats_improvements=ats_payload["improvements"],
            ats_recommendations=ats_payload["recommendations"],
            job_fit_score=job_payload.get("job_fit_score"),
            match_confidence=job_payload.get("match_confidence", 0),
            matching_skills=job_payload.get("matching_skills", []),
            missing_required_skills=job_payload.get("missing_required_skills", []),
            missing_preferred_skills=job_payload.get("missing_preferred_skills", []),
            missing_experience=job_payload.get("missing_experience", []),
            missing_certifications=job_payload.get("missing_certifications", []),
            resume_strengths=job_payload.get("resume_strengths", []),
            resume_weaknesses=job_payload.get("resume_weaknesses", []),
            suggestions=job_payload.get("suggestions", []),
        )

        raw = self._call_with_retry(self._client.explain, prompt)
        if not raw:
            if self._debug_mode:
                logger.info("DEBUG_AI: returning mock explanation")
                return self._mock_explanation(ats_payload, job_payload)
            return None

        explanation = self._validate_explanation(raw, ats_payload, job_payload)
        if explanation:
            cache.set(cache_key, explanation.model_dump(mode="json"), CACHE_TTL)
        return explanation

    def rewrite(
        self,
        ats_payload: dict[str, Any],
        job_payload: dict[str, Any],
        resume_text: str,
    ) -> AIRewrite | None:
        """
        Generate grounded rewrite suggestions for resume sections.

        Args:
            ats_payload: Output from ``calculate_ats_score``.
            job_payload: Output from ``calculate_job_fit``.
            resume_text: Full raw resume text (sent to model for quoting).

        Returns:
            Validated AIRewrite, or None if AI is unavailable or all
            attempts fail validation.
        """
        if not self._enabled:
            return None

        cache_key = self._cache_key("rewrite", ats_payload, job_payload)
        cached = cache.get(cache_key)
        if cached:
            try:
                return AIRewrite.model_validate(cached)
            except Exception:
                logger.debug("Cached rewrite failed validation, recomputing")

        prompt = build_rewrite_context(
            resume_text=resume_text,
            ats_breakdown=ats_payload["breakdown"],
            ats_improvements=ats_payload["improvements"],
            ats_recommendations=ats_payload["recommendations"],
            missing_required_skills=job_payload.get("missing_required_skills", []),
            missing_preferred_skills=job_payload.get("missing_preferred_skills", []),
            missing_experience=job_payload.get("missing_experience", []),
            missing_certifications=job_payload.get("missing_certifications", []),
            suggestions=job_payload.get("suggestions", []),
        )

        raw = self._call_with_retry(self._client.rewrite, prompt)
        if not raw:
            if self._debug_mode:
                logger.info("DEBUG_AI: returning mock rewrite")
                return self._mock_rewrite(ats_payload, job_payload, resume_text)
            return None

        rewrite = self._validate_rewrite(raw, ats_payload, job_payload, resume_text)
        if rewrite:
            cache.set(cache_key, rewrite.model_dump(mode="json"), CACHE_TTL)
        return rewrite

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    def _cache_key(self, op: str, ats_payload: dict, job_payload: dict) -> str:
        """
        Stable cache key derived from the deterministic engine outputs.

        Using the engine payloads (not the raw resume text) means:
        - Same ATS + job-match results = same cache entry (correct)
        - Cache invalidates automatically when engine logic changes
        """
        key_data = {
            "v": CACHE_VERSION,
            "op": op,
            "ats": {
                "score": ats_payload["ats_score"],
                "breakdown": {k: v["score"] for k, v in ats_payload["breakdown"].items()},
            },
            "job": {
                "fit_score": job_payload.get("job_fit_score"),
                "missing_required": job_payload.get("missing_required_skills", []),
                "missing_preferred": job_payload.get("missing_preferred_skills", []),
                "missing_exp": job_payload.get("missing_experience", []),
                "missing_certs": job_payload.get("missing_certifications", []),
            },
        }
        serialized = json.dumps(key_data, sort_keys=True)
        digest = hashlib.sha256(serialized.encode()).hexdigest()[:32]
        return f"{CACHE_PREFIX}:{op}:{digest}"

    def _call_with_retry(self, method, prompt: str, max_attempts: int = 2) -> str | None:
        """
        Call the client method with one retry on validation failure.

        The model sometimes drifts on the first attempt; a second attempt with
        a stricter system reminder often corrects it.
        """
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    # Add a reminder on retry
                    prompt = (
                        prompt
                        + "\n\nIMPORTANT: Your previous response failed validation. "
                        "Output ONLY valid JSON matching the schema. "
                        "Every 'finding'/'target_finding' MUST match the context verbatim."
                    )
                return method(prompt)
            except (AIUnavailable, AIResponseError) as e:
                logger.warning("AI call failed (attempt %d/%d): %s", attempt + 1, max_attempts, e)
                if attempt == max_attempts - 1:
                    return None
        return None

    def _validate_explanation(
        self,
        raw: str,
        ats_payload: dict,
        job_payload: dict,
    ) -> AIExplanation | None:
        """Parse JSON, validate schema, and verify grounding."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning("Explanation response not valid JSON: %s", e)
            return None

        try:
            explanation = AIExplanation.model_validate(data)
        except Exception as e:
            logger.warning("Explanation schema validation failed: %s", e)
            return None

        if not self._ground_explanation(explanation, ats_payload, job_payload):
            logger.warning("Explanation grounding check failed")
            return None

        return explanation

    def _validate_rewrite(
        self,
        raw: str,
        ats_payload: dict,
        job_payload: dict,
        resume_text: str,
    ) -> AIRewrite | None:
        """Parse JSON, validate schema, and verify grounding."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning("Rewrite response not valid JSON: %s", e)
            return None

        try:
            rewrite = AIRewrite.model_validate(data)
        except Exception as e:
            logger.warning("Rewrite schema validation failed: %s", e)
            return None

        if not self._ground_rewrite(rewrite, ats_payload, job_payload, resume_text):
            logger.warning("Rewrite grounding check failed")
            return None

        return rewrite

    # -------------------------------------------------------------------------
    # Grounding checks
    # -------------------------------------------------------------------------
    def _ground_explanation(
        self,
        explanation: AIExplanation,
        ats_payload: dict,
        job_payload: dict,
    ) -> bool:
        """
        Verify every explanation item references a real finding from the engine.

        Allowed sources:
        - ats_payload["improvements"]
        - ats_payload["recommendations"]
        - job_payload["missing_required_skills"]
        - job_payload["missing_preferred_skills"]
        - job_payload["missing_experience"]
        - job_payload["missing_certifications"]
        - job_payload["resume_weaknesses"]
        - job_payload["suggestions"]
        """
        # Build a set of all valid finding strings from the engine payload
        valid_findings = set()
        valid_findings.update(ats_payload.get("improvements", []))
        valid_findings.update(ats_payload.get("recommendations", []))
        valid_findings.update(job_payload.get("missing_required_skills", []))
        valid_findings.update(job_payload.get("missing_preferred_skills", []))
        valid_findings.update(job_payload.get("missing_experience", []))
        valid_findings.update(job_payload.get("missing_certifications", []))
        valid_findings.update(job_payload.get("resume_weaknesses", []))
        valid_findings.update(job_payload.get("suggestions", []))

        # ATS category names are also valid for category-level explanations
        valid_findings.update(ats_payload.get("breakdown", {}).keys())

        for item in explanation.items:
            if item.finding not in valid_findings:
                logger.debug("Ungrounded finding: %r", item.finding)
                return False
        return True

    def _ground_rewrite(
        self,
        rewrite: AIRewrite,
        ats_payload: dict,
        job_payload: dict,
        resume_text: str,
    ) -> bool:
        """
        Verify every rewrite targets a real finding and quotes real resume text.
        """
        valid_findings = set()
        valid_findings.update(ats_payload.get("improvements", []))
        valid_findings.update(ats_payload.get("recommendations", []))
        valid_findings.update(job_payload.get("missing_required_skills", []))
        valid_findings.update(job_payload.get("missing_preferred_skills", []))
        valid_findings.update(job_payload.get("missing_experience", []))
        valid_findings.update(job_payload.get("missing_certifications", []))
        valid_findings.update(job_payload.get("suggestions", []))

        for suggestion in rewrite.suggestions:
            # Target finding must be grounded
            if suggestion.target_finding not in valid_findings:
                logger.debug("Ungrounded target_finding: %r", suggestion.target_finding)
                return False

            # Original text must exist in resume (or be "N/A" for missing sections)
            if suggestion.original != "N/A" and suggestion.original not in resume_text:
                logger.debug("Original text not found in resume: %r", suggestion.original[:80])
                return False

        return True

    # -------------------------------------------------------------------------
    # Debug mock data (only used when DEBUG_AI=True and real API fails)
    # -------------------------------------------------------------------------
    def _mock_explanation(self, ats_payload: dict, job_payload: dict) -> AIExplanation:
        """Generate a grounded mock explanation for development."""
        missing_required = job_payload.get("missing_required_skills", [])
        missing_preferred = job_payload.get("missing_preferred_skills", [])
        missing_exp = job_payload.get("missing_experience", [])
        improvements = ats_payload.get("improvements", [])
        recommendations = ats_payload.get("recommendations", [])

        items = []

        # Missing required skills
        for skill in missing_required[:3]:
            items.append(ExplanationItem(
                category="missing_required_skills",
                finding=skill,
                plain_language=f"The job requires '{skill}' but it is missing from your resume.",
                action=f"Add '{skill}' to your Skills section or highlight it in your experience.",
                priority="high",
            ))

        # Missing preferred skills
        for skill in missing_preferred[:2]:
            items.append(ExplanationItem(
                category="missing_preferred_skills",
                finding=skill,
                plain_language=f"The job prefers '{skill}' but it is not on your resume.",
                action=f"Consider adding '{skill}' if you have experience with it.",
                priority="medium",
            ))

        # Missing experience
        for exp in missing_exp[:1]:
            items.append(ExplanationItem(
                category="missing_experience",
                finding=exp,
                plain_language=f"Your experience level may not meet the job's requirements.",
                action="Emphasize depth and impact in your work experience bullets.",
                priority="high",
            ))

        # ATS improvements
        for imp in improvements[:2]:
            items.append(ExplanationItem(
                category="ATS Improvements",
                finding=imp,
                plain_language=f"ATS detected: {imp}. This may lower your score.",
                action=f"Address: {imp}",
                priority="medium",
            ))

        # ATS recommendations
        for rec in recommendations[:1]:
            items.append(ExplanationItem(
                category="ATS Recommendations",
                finding=rec,
                plain_language=f"Recommendation: {rec}",
                action=rec,
                priority="low",
            ))

        # Limit to 12 items
        items = items[:12]

        # Summary
        fit_score = job_payload.get("job_fit_score", 0)
        if missing_required:
            biggest_gap = f"missing required skills: {', '.join(missing_required[:3])}"
        elif missing_exp:
            biggest_gap = "experience gap"
        else:
            biggest_gap = "strong match"

        summary = (
            f"Your resume scores {fit_score}/100 for this role. "
            f"The biggest gap is {biggest_gap}. "
            f"Focus on the high-priority items above to improve your fit."
        )

        return AIExplanation(items=items, summary=summary)

    def _mock_rewrite(self, ats_payload: dict, job_payload: dict, resume_text: str) -> AIRewrite:
        """Generate a grounded mock rewrite for development."""
        missing_required = job_payload.get("missing_required_skills", [])
        missing_preferred = job_payload.get("missing_preferred_skills", [])
        improvements = ats_payload.get("improvements", [])
        suggestions = job_payload.get("suggestions", [])

        suggestions_list = []

        # Find a section in the resume to use as "original"
        # Try to find Skills section
        skills_original = "N/A"
        lines = resume_text.split('\n')
        for i, line in enumerate(lines):
            if 'skill' in line.lower() and i + 1 < len(lines):
                skills_original = lines[i + 1].strip() or "N/A"
                break

        # Skills rewrite
        if missing_required or missing_preferred:
            all_missing = missing_required + missing_preferred
            if skills_original != "N/A" and skills_original in resume_text:
                suggestions_list.append(RewriteSuggestion(
                    section="Skills",
                    original=skills_original,
                    rewritten=f"{skills_original}, {', '.join(all_missing[:4])}",
                    target_finding=all_missing[0] if all_missing else (missing_required[0] if missing_required else missing_preferred[0]),
                    rationale=f"Adds missing required/preferred skills from the job description.",
                ))
            elif skills_original == "N/A":
                # Resume has no Skills section - suggest adding one
                suggestions_list.append(RewriteSuggestion(
                    section="Skills",
                    original="N/A",
                    rewritten=f"{', '.join(all_missing[:4])}",
                    target_finding=all_missing[0] if all_missing else (missing_required[0] if missing_required else missing_preferred[0]),
                    rationale="Adds a Skills section with required/preferred skills from the job description.",
                ))

        # Professional Summary rewrite
        summary_original = "N/A"
        for i, line in enumerate(lines):
            if 'summary' in line.lower() and i + 1 < len(lines):
                summary_original = lines[i + 1].strip() or "N/A"
                break
        if summary_original != "N/A" and summary_original in resume_text:
            suggestions_list.append(RewriteSuggestion(
                section="Professional Summary",
                original=summary_original,
                rewritten=f"{summary_original} Experienced in {', '.join(missing_required[:2]) if missing_required else 'key technologies'}.",
                target_finding=suggestions[0] if suggestions else (missing_required[0] if missing_required else "skills gap"),
                rationale="Incorporates missing keywords into the professional summary for ATS visibility.",
            ))
        elif summary_original == "N/A":
            # Resume has no Summary section - suggest adding one
            suggestions_list.append(RewriteSuggestion(
                section="Professional Summary",
                original="N/A",
                rewritten=f"Experienced professional skilled in {', '.join(missing_required[:3]) if missing_required else 'relevant technologies'}.",
                target_finding=suggestions[0] if suggestions else (missing_required[0] if missing_required else "skills gap"),
                rationale="Adds a professional summary with target keywords for ATS visibility.",
            ))

        # Work Experience rewrite - if we have missing experience
        missing_exp = job_payload.get("missing_experience", [])
        if missing_exp:
            exp_original = "N/A"
            for i, line in enumerate(lines):
                if 'experience' in line.lower() or 'work' in line.lower():
                    if i + 1 < len(lines):
                        exp_original = lines[i + 1].strip() or "N/A"
                        break
            if exp_original != "N/A" and exp_original in resume_text:
                suggestions_list.append(RewriteSuggestion(
                    section="Work Experience",
                    original=exp_original,
                    rewritten=f"{exp_original}\n- Led projects using {missing_required[0] if missing_required else 'required technologies'}",
                    target_finding=missing_exp[0],
                    rationale="Addresses experience gap by quantifying relevant project work.",
                ))
            elif exp_original == "N/A":
                # Resume has no Work Experience section - suggest adding one
                suggestions_list.append(RewriteSuggestion(
                    section="Work Experience",
                    original="N/A",
                    rewritten=f"Software Engineer\n- Led projects using {missing_required[0] if missing_required else 'required technologies'}",
                    target_finding=missing_exp[0],
                    rationale="Adds work experience section addressing the experience gap.",
                ))

        # Fallback: if no suggestions generated at all, create a generic one
        if not suggestions_list and (missing_required or missing_preferred or missing_exp):
            target = missing_required[0] if missing_required else (missing_preferred[0] if missing_preferred else missing_exp[0])
            suggestions_list.append(RewriteSuggestion(
                section="Skills",
                original="N/A",
                rewritten=f"{target}",
                target_finding=target,
                rationale="Adds the most critical missing skill from the job description.",
            ))

        # Limit to 8
        suggestions_list = suggestions_list[:8]

        note = "These are mock AI suggestions (DEBUG_AI mode). Configure a valid OpenAI API key for real AI analysis."

        return AIRewrite(suggestions=suggestions_list, note=note)


# -----------------------------------------------------------------------------
# Module-level singleton for convenience (Django app lifecycle is long-lived)
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    """Return a cached AIService instance (created on first call)."""
    return AIService()