"""
Resume analysis service layer.

Owns the full analysis pipeline (PDF bytes -> text -> ResumeDocument -> ATS ->
job match -> statistics) so Django views stay thin. Also implements the
resume_json cache: a cache key derived from the PDF bytes + job description is
persisted with the results, and a request whose key matches the stored one can
render straight from the cache instead of re-parsing and re-scoring.

All return values are plain JSON-serializable data (no model instances, no
datetimes) so the payload can be stored in ResumeAnalysis.resume_json.
"""
import hashlib
import logging

from .analyzer import analyze
from .ats_engine import calculate_ats_score
from .job_matcher import calculate_job_fit
from .text_extractor import parse_pdf
from .utils import detect_skills, resume_statistics

logger = logging.getLogger(__name__)

# Bump when the analysis logic changes enough that old cached results should
# be discarded (stale caches are ignored on a key match).
CACHE_VERSION = 1


def read_file_bytes(file_obj):
    """
    Read a file object's bytes safely.

    Returns bytes, or None when the file cannot be read (missing from storage,
    corrupted, permission error). The caller decides how to degrade.
    """
    try:
        file_obj.open("rb")
        data = file_obj.read()
        file_obj.close()
        return data
    except Exception:
        logger.exception("Failed to read file bytes for %r", getattr(file_obj, "name", None))
        return None


def build_cache_key(pdf_bytes, job_description):
    """Stable key identifying one (pdf, job description) analysis."""
    jd = (job_description or "").encode("utf-8")
    return hashlib.sha1(pdf_bytes + jd).hexdigest()


def run_analysis_pipeline(pdf_bytes, job_description):
    """
    Execute the full analysis in a single pass.

    Returns:
        (context, payload)
        context: dict of display data for the analysis template.
        payload: dict persisted to ResumeAnalysis.resume_json (includes the
                 cache key under "_meta").
    """
    parsed = parse_pdf(pdf_bytes)
    text = parsed["text"]

    # Single parse shared by every scoring stage.
    doc = analyze(
        text,
        is_scanned=parsed["is_scanned"],
        page_count=parsed["page_count"],
    )
    ats = calculate_ats_score(text, doc=doc)
    job = calculate_job_fit(ats["detected_skills"], job_description, doc=doc)

    found_skills, missing_skills = detect_skills(text)
    stats = resume_statistics(text)

    payload = {
        "_meta": {
            "cache_key": build_cache_key(pdf_bytes, job_description),
            "version": CACHE_VERSION,
        },
        "text": text,
        "is_scanned": parsed["is_scanned"],
        "page_count": parsed["page_count"],
        "stats": stats,
        "found_skills": found_skills,
        "missing_skills": missing_skills,
        "ats": ats,
        "job": job,
    }

    return _build_context(payload), payload


def context_from_payload(payload):
    """Reconstruct the render context from a stored resume_json payload."""
    return _build_context(payload)


def _build_context(payload):
    """Turn a payload into the context dict the analysis template expects."""
    ats = payload["ats"]
    ats_breakdown_progress = [
        {
            "category": category,
            "score": detail["score"],
            "percent": round((detail["score"] / detail["max"]) * 100)
            if detail["max"]
            else 0,
        }
        for category, detail in ats["breakdown"].items()
    ]

    job = payload["job"]
    stats = payload["stats"]

    return {
        "text": payload["text"],
        "is_scanned": payload["is_scanned"],
        "page_count": payload["page_count"],
        "word_count": stats["word_count"],
        "character_count": stats["character_count"],
        "found_skills": payload["found_skills"],
        "missing_skills": payload["missing_skills"],
        # ATS
        "ats_score": ats["ats_score"],
        "grade": ats["grade"],
        "ats_breakdown": ats_breakdown_progress,
        "strengths": ats["strengths"],
        "improvements": ats["improvements"],
        "recommendations": ats["recommendations"],
        # Job match
        "job_fit_score": job["job_fit_score"],
        "matching_skills": job["matching_skills"],
        "job_missing_skills": job["missing_skills"],
        "extra_skills": job["extra_skills"],
        "job_recommendations": job["recommendations"],
    }