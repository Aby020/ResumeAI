"""
ResumeAI AI layer.

This package is deliberately isolated from the deterministic analysis
engines (``ats_engine``, ``job_matcher``, ``analyzer``). Those engines stay
the single source of truth for scores and matches. Everything in ``ai`` only
*explains* those results in plain language and *rewrites* resume text to act
on their suggestions — it never computes or overrides a score.

Public surface:
    AIService          - orchestrates explain/rewrite with caching + grounding
    OpenAIClient       - thin wrapper over the official OpenAI SDK
    AIExplanation      - validated structured explanation (pydantic)
    AIRewrite          - validated structured rewrite (pydantic)
    AIUnavailable      - raised when no API key / provider is unreachable
    AIResponseError    - raised when the provider returns unusable output

See ``service.py`` for usage.
"""
from .client import AIResponseError, AIUnavailable, OpenAIClient
from .schemas import (
    AIExplanation,
    AIRewrite,
    ExplanationItem,
    RewriteSuggestion,
)
from .service import AIService, get_ai_service

__all__ = [
    "AIService",
    "OpenAIClient",
    "AIExplanation",
    "AIRewrite",
    "ExplanationItem",
    "RewriteSuggestion",
    "AIUnavailable",
    "AIResponseError",
    "get_ai_service",
]
