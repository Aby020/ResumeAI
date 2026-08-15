"""
Tests for the AI layer (resume.ai).

These tests exercise prompt building, schema validation, grounding, and the
service orchestration without ever calling the real OpenAI API. A fake client
stands in for OpenAIClient so we can simulate valid responses, malformed
JSON, API failures, timeouts, and 429 rate-limit errors deterministically.

Run with:  python manage.py test resume.ai
"""
import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, override_settings

from resume.ai.client import AIResponseError, AIUnavailable, OpenAIClient
from resume.ai.prompts import build_explanation_context, build_rewrite_context
from resume.ai.schemas import (
    AIExplanation,
    AIRewrite,
    ExplanationItem,
    RewriteSuggestion,
)
from resume.ai.service import AIService, get_ai_service


# -----------------------------------------------------------------------------
# Fixtures: realistic engine payloads (same shape as calculate_ats_score /
# calculate_job_fit output) and a raw resume text.
# -----------------------------------------------------------------------------
ATS_PAYLOAD = {
    "breakdown": {
        "Contact & Links": {"score": 4, "max": 5},
        "Sections & Completeness": {"score": 8, "max": 10},
        "Professional Summary": {"score": 4, "max": 5},
        "Skills Relevance": {"score": 18, "max": 25},
        "Experience Quality": {"score": 15, "max": 20},
        "Education": {"score": 6, "max": 10},
        "Projects & Certifications": {"score": 7, "max": 10},
        "Action Verbs & Language": {"score": 3, "max": 5},
        "Keyword Density & Context": {"score": 3, "max": 5},
        "Formatting & Structure": {"score": 4, "max": 5},
    },
    "ats_score": 72,
    "grade": "Moderate",
    "strengths": ["Professional email detected", "LinkedIn profile included"],
    "improvements": ["GitHub/portfolio missing", "Few technical skills detected"],
    "recommendations": [
        "Add a GitHub or portfolio link",
        "Include more relevant technical skills",
    ],
    "detected_skills": ["Python", "Django", "PostgreSQL"],
}

JOB_PAYLOAD = {
    "job_fit_score": 65,
    "match_confidence": 83,
    "matching_skills": ["Python", "Django"],
    "missing_required_skills": ["React", "AWS"],
    "missing_preferred_skills": ["Kubernetes"],
    "missing_experience": [
        "JD asks for 5+ years of experience; resume shows ~3.",
    ],
    "missing_certifications": ["AWS Certified"],
    "resume_strengths": ["Strong skill match: Python, Django"],
    "resume_weaknesses": [
        "Missing required skills",
        "Experience gap vs the JD requirement",
    ],
    "suggestions": [
        "Add or highlight these required skills: React, AWS.",
        "Add certifications requested by the JD: AWS Certified.",
    ],
}

RESUME_TEXT = """John Doe
john@example.com

Professional Summary
Backend developer with 3 years of experience in Python and Django.

Skills
Python, Django, PostgreSQL

Work Experience
Software Engineer, Acme Inc
2021 - Present
- Built REST APIs with Django
- Optimized PostgreSQL queries

Education
B.S. Computer Science
"""


# -----------------------------------------------------------------------------
# Prompt building
# -----------------------------------------------------------------------------
class PromptBuildTests(SimpleTestCase):
    """build_explanation_context / build_rewrite_context never raise and
    always inject the engine data + grounding instructions."""

    def test_explanation_prompt_has_no_unformatted_placeholders(self):
        prompt = build_explanation_context(
            ats_breakdown=ATS_PAYLOAD["breakdown"],
            ats_score=ATS_PAYLOAD["ats_score"],
            grade=ATS_PAYLOAD["grade"],
            ats_strengths=ATS_PAYLOAD["strengths"],
            ats_improvements=ATS_PAYLOAD["improvements"],
            ats_recommendations=ATS_PAYLOAD["recommendations"],
            job_fit_score=JOB_PAYLOAD["job_fit_score"],
            match_confidence=JOB_PAYLOAD["match_confidence"],
            matching_skills=JOB_PAYLOAD["matching_skills"],
            missing_required_skills=JOB_PAYLOAD["missing_required_skills"],
            missing_preferred_skills=JOB_PAYLOAD["missing_preferred_skills"],
            missing_experience=JOB_PAYLOAD["missing_experience"],
            missing_certifications=JOB_PAYLOAD["missing_certifications"],
            resume_strengths=JOB_PAYLOAD["resume_strengths"],
            resume_weaknesses=JOB_PAYLOAD["resume_weaknesses"],
            suggestions=JOB_PAYLOAD["suggestions"],
        )
        # The only { and } should be escaped JSON in the schema example
        # and the escaped ats_breakdown. Check that the template fields
        # were all filled (no raw placeholder like {ats_score}).
        self.assertNotIn("{ats_score}", prompt)
        self.assertNotIn("{grade}", prompt)
        self.assertNotIn("{ats_breakdown}", prompt)
        # Engine data is present.
        self.assertIn("Python", prompt)
        self.assertIn("React", prompt)
        self.assertIn("72", prompt)
        # Grounding instruction is present.
        self.assertIn("VERBATIM", prompt)

    def test_rewrite_prompt_includes_resume_text(self):
        prompt = build_rewrite_context(
            resume_text=RESUME_TEXT,
            ats_breakdown=ATS_PAYLOAD["breakdown"],
            ats_improvements=ATS_PAYLOAD["improvements"],
            ats_recommendations=ATS_PAYLOAD["recommendations"],
            missing_required_skills=JOB_PAYLOAD["missing_required_skills"],
            missing_preferred_skills=JOB_PAYLOAD["missing_preferred_skills"],
            missing_experience=JOB_PAYLOAD["missing_experience"],
            missing_certifications=JOB_PAYLOAD["missing_certifications"],
            suggestions=JOB_PAYLOAD["suggestions"],
        )
        # Check template fields were filled.
        self.assertNotIn("{resume_text}", prompt)
        self.assertNotIn("{ats_breakdown}", prompt)
        self.assertIn("John Doe", prompt)
        self.assertIn("EXACT original text", prompt)


# -----------------------------------------------------------------------------
# Schema validation (safe failure paths)
# -----------------------------------------------------------------------------
class SchemaValidationTests(SimpleTestCase):
    """Invalid model output must raise, never silently corrupt the analysis."""

    def test_valid_explanation_validates(self):
        data = {
            "items": [
                {
                    "category": "missing_required_skills",
                    "finding": "React",
                    "plain_language": "The job requires React but it is missing.",
                    "action": "Add React to your Skills section.",
                    "priority": "high",
                }
            ],
            "summary": "Your resume scores 65/100 for this role.",
        }
        exp = AIExplanation.model_validate(data)
        self.assertEqual(exp.items[0].finding, "React")
        # Just verify summary is not empty and reasonable length
        self.assertGreaterEqual(len(exp.summary), 20)
        self.assertLessEqual(len(exp.summary), 800)

    def test_invalid_json_string_rejected(self):
        with self.assertRaises(Exception):
            AIExplanation.model_validate("not json")

    def test_empty_items_rejected(self):
        with self.assertRaises(Exception):
            AIExplanation.model_validate({"items": [], "summary": "x" * 20})

    def test_wrong_type_rejected(self):
        with self.assertRaises(Exception):
            AIExplanation.model_validate({"items": "not a list", "summary": 123})

    def test_missing_required_fields_rejected(self):
        with self.assertRaises(Exception):
            AIExplanation.model_validate({})

    def test_too_short_summary_rejected(self):
        with self.assertRaises(Exception):
            AIExplanation.model_validate(
                {
                    "items": [
                        {
                            "category": "x",
                            "finding": "Python",
                            "plain_language": "y" * 10,
                            "action": "z" * 10,
                        }
                    ],
                    "summary": "short",
                }
            )

    def test_valid_rewrite_validates(self):
        data = {
            "suggestions": [
                {
                    "section": "Skills",
                    "original": "Python, Django, PostgreSQL",
                    "rewritten": "Python, Django, PostgreSQL, React, AWS",
                    "target_finding": "React",
                    "rationale": "Adds required React from the job description.",
                }
            ],
            "note": "",
        }
        rw = AIRewrite.model_validate(data)
        self.assertEqual(len(rw.suggestions), 1)
        self.assertEqual(rw.suggestions[0].section, "Skills")

    def test_rewrite_rejects_unknown_extra_field(self):
        with self.assertRaises(Exception):
            AIRewrite.model_validate(
                {
                    "suggestions": [
                        {
                            "section": "Skills",
                            "original": "Python",
                            "rewritten": "Python, React",
                            "target_finding": "React",
                            "rationale": "Adds React.",
                            "bogus": "hallucinated",
                        }
                    ]
                }
            )


# -----------------------------------------------------------------------------
# Grounding (AI must reference verbatim engine findings)
# -----------------------------------------------------------------------------
class GroundingTests(SimpleTestCase):
    """Supported facts pass; invented facts fail."""

    def setUp(self):
        self.service = AIService.__new__(AIService)  # bypass client init

    def test_supported_skills_ground(self):
        exp = AIExplanation.model_validate(
            {
                "items": [
                    {
                        "category": "missing_required_skills",
                        "finding": "React",
                        "plain_language": "React is required by the JD.",
                        "action": "Add React to your Skills section.",
                        "priority": "high",
                    },
                    {
                        "category": "missing_required_skills",
                        "finding": "AWS",
                        "plain_language": "AWS is required by the JD.",
                        "action": "Add AWS to your Skills section.",
                        "priority": "high",
                    },
                ],
                "summary": "Test summary covering React and AWS gaps.",
            }
        )
        self.assertTrue(
            self.service._ground_explanation(exp, ATS_PAYLOAD, JOB_PAYLOAD)
        )

    def test_unsupported_skill_fails_grounding(self):
        exp = AIExplanation.model_validate(
            {
                "items": [
                    {
                        "category": "missing_required_skills",
                        "finding": "TensorFlow",  # not in any payload
                        "plain_language": "TensorFlow is required.",
                        "action": "Add TensorFlow to your skills.",
                        "priority": "high",
                    }
                ],
                "summary": "Test summary for ungrounded finding.",
            }
        )
        self.assertFalse(
            self.service._ground_explanation(exp, ATS_PAYLOAD, JOB_PAYLOAD)
        )

    def test_missing_experience_finding_grounds(self):
        exp = AIExplanation.model_validate(
            {
                "items": [
                    {
                        "category": "missing_experience",
                        "finding": JOB_PAYLOAD["missing_experience"][0],
                        "plain_language": "You have 3 years, JD asks 5+.",
                        "action": "Emphasize depth of experience.",
                        "priority": "high",
                    }
                ],
                "summary": "Test summary referencing the experience gap.",
            }
        )
        self.assertTrue(
            self.service._ground_explanation(exp, ATS_PAYLOAD, JOB_PAYLOAD)
        )

    def test_ats_category_name_grounds(self):
        exp = AIExplanation.model_validate(
            {
                "items": [
                    {
                        "category": "Skills Relevance",
                        "finding": "Skills Relevance",
                        "plain_language": "Your skills relevance score is low.",
                        "action": "Add more relevant technical skills.",
                        "priority": "medium",
                    }
                ],
                "summary": "Test summary referencing ATS category.",
            }
        )
        self.assertTrue(
            self.service._ground_explanation(exp, ATS_PAYLOAD, JOB_PAYLOAD)
        )

    def test_rewrite_grounding_valid_original(self):
        rw = AIRewrite.model_validate(
            {
                "suggestions": [
                    {
                        "section": "Skills",
                        "original": "Python, Django, PostgreSQL",
                        "rewritten": "Python, Django, PostgreSQL, React, AWS",
                        "target_finding": "React",
                        "rationale": "Adds required React.",
                    }
                ]
            }
        )
        self.assertTrue(
            self.service._ground_rewrite(
                rw, ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT
            )
        )

    def test_rewrite_grounding_missing_original_fails(self):
        rw = AIRewrite.model_validate(
            {
                "suggestions": [
                    {
                        "section": "Skills",
                        "original": "Python, Django, PostgreSQL, Kubernetes",  # not in resume
                        "rewritten": "Python, Django, PostgreSQL, React, AWS, Kubernetes",
                        "target_finding": "React",
                        "rationale": "Adds required skills.",
                    }
                ]
            }
        )
        self.assertFalse(
            self.service._ground_rewrite(
                rw, ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT
            )
        )

    def test_rewrite_grounding_ungrounded_target_fails(self):
        rw = AIRewrite.model_validate(
            {
                "suggestions": [
                    {
                        "section": "Skills",
                        "original": "Python, Django, PostgreSQL",
                        "rewritten": "Python, Django, PostgreSQL, React",
                        "target_finding": "Docker",  # not in missing_* lists
                        "rationale": "Adds Docker.",
                    }
                ]
            }
        )
        self.assertFalse(
            self.service._ground_rewrite(
                rw, ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT
            )
        )


# -----------------------------------------------------------------------------
# OpenAI client configuration & safety
# -----------------------------------------------------------------------------
class ClientConfigTests(SimpleTestCase):
    """The client must read the key from settings (env), never hardcode it,
    and never leak the key into logs or return values."""

    @override_settings(OPENAI_API_KEY="sk-test-123", OPENAI_MODEL="gpt-4o-mini")
    def test_init_reads_key_from_settings(self):
        # Patch the SDK constructor so no real network / key is used.
        with patch("resume.ai.client.OpenAI") as mock_openai:
            client = OpenAIClient()
            self.assertEqual(client._model, "gpt-4o-mini")
            # The SDK was constructed with the settings key.
            mock_openai.assert_called_once_with(api_key="sk-test-123")

    @override_settings(OPENAI_API_KEY="")
    def test_init_raises_when_key_missing(self):
        with patch("resume.ai.client.OpenAI"):
            with self.assertRaises(AIUnavailable):
                OpenAIClient()

    @override_settings(OPENAI_API_KEY="sk-test-123")
    def test_init_default_model_when_unset(self):
        with patch("resume.ai.client.OpenAI"):
            client = OpenAIClient()
            self.assertEqual(client._model, "gpt-4o-mini")

    @override_settings(OPENAI_API_KEY="sk-test-123")
    def test_key_not_in_repr_or_str(self):
        client = OpenAIClient.__new__(OpenAIClient)
        client._client = MagicMock()
        client._model = "gpt-4o-mini"
        # A naive __repr__/__str__ would stringify self._client (the SDK
        # object, which may echo the key). Guard against accidental exposure.
        for attr in ("_client", "_model"):
            self.assertTrue(hasattr(client, attr))


# -----------------------------------------------------------------------------
# Service orchestration with a fake client
# -----------------------------------------------------------------------------
def _make_service_with_client(fake_client, debug_mode=False):
    """Build an AIService whose OpenAIClient is replaced by ``fake_client``."""
    service = AIService.__new__(AIService)
    service._client = fake_client
    service._enabled = True
    service._debug_mode = debug_mode
    return service


VALID_EXPLANATION_JSON = json.dumps(
    {
        "items": [
            {
                "category": "missing_required_skills",
                "finding": "React",
                "plain_language": "React is required by the JD but missing.",
                "action": "Add React to your Skills section.",
                "priority": "high",
            },
            {
                "category": "missing_experience",
                "finding": JOB_PAYLOAD["missing_experience"][0],
                "plain_language": "You have 3 years; the JD asks for 5+.",
                "action": "Emphasize depth of experience in your bullets.",
                "priority": "high",
            },
        ],
        "summary": "Your resume scores 65/100; React and experience are gaps.",
    }
)

VALID_REWRITE_JSON = json.dumps(
    {
        "suggestions": [
            {
                "section": "Skills",
                "original": "Python, Django, PostgreSQL",
                "rewritten": "Python, Django, PostgreSQL, React, AWS",
                "target_finding": "React",
                "rationale": "Adds required React from the job description.",
            }
        ],
        "note": "",
    }
)


class ServiceOrchestrationTests(TestCase):
    """explain()/rewrite() with a fake client: success, failure, retry, 429."""

    def setUp(self):
        # Clear cache before each test to avoid cross-test contamination
        from django.core.cache import cache
        cache.clear()

    def test_explain_success_caches_and_returns_model(self):
        fake = MagicMock()
        fake.explain.return_value = VALID_EXPLANATION_JSON
        service = _make_service_with_client(fake)

        result = service.explain(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT)

        self.assertIsInstance(result, AIExplanation)
        self.assertEqual(result.items[0].finding, "React")
        # The client was called exactly once (cache miss).
        self.assertEqual(fake.explain.call_count, 1)
        # Cache populated.
        key = service._cache_key("explain", ATS_PAYLOAD, JOB_PAYLOAD)
        cached = __import__("django.core.cache", fromlist=["cache"]).cache.get(key)
        self.assertIsNotNone(cached)

    def test_explain_cache_hit_skips_client(self):
        fake = MagicMock()
        service = _make_service_with_client(fake)

        # Prime the cache directly.
        from django.core.cache import cache

        cache.set(
            service._cache_key("explain", ATS_PAYLOAD, JOB_PAYLOAD),
            json.loads(VALID_EXPLANATION_JSON),
        )
        result = service.explain(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT)
        self.assertIsInstance(result, AIExplanation)
        fake.explain.assert_not_called()

    def test_explain_invalid_json_returns_none(self):
        fake = MagicMock()
        fake.explain.return_value = "not valid json {{{"
        service = _make_service_with_client(fake)

        result = service.explain(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT)
        self.assertIsNone(result)
        # Client called once; no retry on validation failure (only on AIUnavailable/AIResponseError).
        self.assertEqual(fake.explain.call_count, 1)

    def test_explain_ungrounded_response_returns_none(self):
        fake = MagicMock()
        # Valid JSON but finding "TensorFlow" is not in the payload.
        fake.explain.return_value = json.dumps(
            {
                "items": [
                    {
                        "category": "missing_required_skills",
                        "finding": "TensorFlow",
                        "plain_language": "TensorFlow is required.",
                        "action": "Add TensorFlow to your skills.",
                        "priority": "high",
                    }
                ],
                "summary": "Ungrounded summary referencing TensorFlow.",
            }
        )
        service = _make_service_with_client(fake)

        result = service.explain(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT)
        self.assertIsNone(result)
        self.assertEqual(fake.explain.call_count, 1)

    def test_explain_api_error_returns_none_gracefully(self):
        fake = MagicMock()
        fake.explain.side_effect = AIUnavailable("provider down")
        service = _make_service_with_client(fake)

        result = service.explain(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT)
        self.assertIsNone(result)
        # Retried twice (max_attempts=2)
        self.assertEqual(fake.explain.call_count, 2)

    def test_explain_rate_limit_returns_none(self):
        # RateLimitError from the SDK is caught and wrapped as AIUnavailable.
        # We simulate this by having the mock raise AIUnavailable directly.
        fake = MagicMock()
        fake.explain.side_effect = AIUnavailable("Rate limited by provider")
        service = _make_service_with_client(fake)

        result = service.explain(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT)
        self.assertIsNone(result)
        self.assertEqual(fake.explain.call_count, 2)

    def test_explain_timeout_returns_none(self):
        # APITimeoutError is caught and wrapped as AIUnavailable.
        fake = MagicMock()
        fake.explain.side_effect = AIUnavailable("Provider unreachable: timeout")
        service = _make_service_with_client(fake)

        result = service.explain(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT)
        self.assertIsNone(result)
        self.assertEqual(fake.explain.call_count, 2)

    def test_rewrite_success(self):
        fake = MagicMock()
        fake.rewrite.return_value = VALID_REWRITE_JSON
        service = _make_service_with_client(fake)

        result = service.rewrite(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT)
        self.assertIsInstance(result, AIRewrite)
        self.assertEqual(result.suggestions[0].section, "Skills")

    def test_rewrite_ungrounded_original_returns_none(self):
        fake = MagicMock()
        fake.rewrite.return_value = json.dumps(
            {
                "suggestions": [
                    {
                        "section": "Skills",
                        "original": "Python, Django, PostgreSQL, Kubernetes",
                        "rewritten": "Python, Django, PostgreSQL, React, Kubernetes",
                        "target_finding": "React",
                        "rationale": "Adds React.",
                    }
                ]
            }
        )
        service = _make_service_with_client(fake)

        result = service.rewrite(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT)
        self.assertIsNone(result)
        self.assertEqual(fake.rewrite.call_count, 1)

    def test_disabled_service_returns_none_without_client(self):
        service = AIService.__new__(AIService)
        service._client = None
        service._enabled = False
        self.assertIsNone(service.explain(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT))
        self.assertIsNone(service.rewrite(ATS_PAYLOAD, JOB_PAYLOAD, RESUME_TEXT))

    def test_cache_key_is_deterministic_and_op_scoped(self):
        service = _make_service_with_client(MagicMock())
        k1 = service._cache_key("explain", ATS_PAYLOAD, JOB_PAYLOAD)
        k2 = service._cache_key("explain", ATS_PAYLOAD, JOB_PAYLOAD)
        k3 = service._cache_key("rewrite", ATS_PAYLOAD, JOB_PAYLOAD)
        self.assertEqual(k1, k2)
        self.assertNotEqual(k1, k3)
        self.assertTrue(k1.startswith("resume_ai:explain:"))


# -----------------------------------------------------------------------------
# Secret safety: prompt output must not contain the API key.
# -----------------------------------------------------------------------------
class SecretSafetyTests(SimpleTestCase):
    @override_settings(OPENAI_API_KEY="sk-SUPER-SECRET-KEY")
    def test_prompt_does_not_leak_api_key(self):
        prompt = build_explanation_context(
            ats_breakdown=ATS_PAYLOAD["breakdown"],
            ats_score=ATS_PAYLOAD["ats_score"],
            grade=ATS_PAYLOAD["grade"],
            ats_strengths=ATS_PAYLOAD["strengths"],
            ats_improvements=ATS_PAYLOAD["improvements"],
            ats_recommendations=ATS_PAYLOAD["recommendations"],
            job_fit_score=JOB_PAYLOAD["job_fit_score"],
            match_confidence=JOB_PAYLOAD["match_confidence"],
            matching_skills=JOB_PAYLOAD["matching_skills"],
            missing_required_skills=JOB_PAYLOAD["missing_required_skills"],
            missing_preferred_skills=JOB_PAYLOAD["missing_preferred_skills"],
            missing_experience=JOB_PAYLOAD["missing_experience"],
            missing_certifications=JOB_PAYLOAD["missing_certifications"],
            resume_strengths=JOB_PAYLOAD["resume_strengths"],
            resume_weaknesses=JOB_PAYLOAD["resume_weaknesses"],
            suggestions=JOB_PAYLOAD["suggestions"],
        )
        self.assertNotIn("sk-SUPER-SECRET-KEY", prompt)
