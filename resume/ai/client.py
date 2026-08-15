"""
Thin wrapper over the official OpenAI Python SDK.

Isolates the rest of the AI layer from SDK details (model names, parameter
shapes, error types, retry/timeout policy). Callers depend only on the
two async methods defined here.

Environment:
    OPENAI_API_KEY  - required; read from .env via python-decouple at Django
                       startup and passed into the client constructor.
    OPENAI_MODEL    - optional, defaults to "gpt-4o-mini" (cheap, fast, strong
                       instruction-following). Override for different cost/
                       latency/capability trade-offs.

Exceptions (public):
    AIUnavailable         - no API key configured or provider unreachable
    AIResponseError       - provider returned something we cannot validate
"""
import os
import logging
from typing import Any

from openai import OpenAI
from openai import APIError, APIConnectionError, APITimeoutError, RateLimitError

from django.conf import settings

logger = logging.getLogger(__name__)


class AIUnavailable(Exception):
    """Raised when the OpenAI client cannot be created or reached."""


class AIResponseError(Exception):
    """Raised when the provider returns output that fails validation."""


class OpenAIClient:
    """
    Async-capable wrapper around the OpenAI chat completions endpoint.

    The public methods are thin async facades; the underlying SDK calls are
    synchronous so they run in a thread pool (handled by callers via
    ``sync_to_async`` or Django's async views). This keeps the wrapper
    simple while not blocking the event loop in async contexts.

    All responses are validated against pydantic models in ``schemas.py``
    before being returned.
    """

    # Model used when OPENAI_MODEL is not set. gpt-4o-mini is the recommended
    # default for production workloads: strong instruction-following, 128k
    # context, and ~1/10 the cost of gpt-4o.
    DEFAULT_MODEL = "gpt-4o-mini"

    # Temperature for explanation/rewrite tasks: low keeps output factual and
    # grounded in the provided context (ATS/job-match JSON).
    DEFAULT_TEMPERATURE = 0.2

    # Max tokens per call. Explanations fit in ~800; rewrites may need ~1500.
    DEFAULT_MAX_TOKENS = 1600

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Args:
            api_key: OpenAI API key. If None, reads from ``settings.OPENAI_API_KEY``
                     (populated by python-decouple from .env).
            model:   Model name override. Defaults to ``DEFAULT_MODEL``.
        """
        resolved_key = api_key or getattr(settings, "OPENAI_API_KEY", None)
        if not resolved_key:
            raise AIUnavailable("OPENAI_API_KEY not configured in environment")

        self._client = OpenAI(api_key=resolved_key)
        self._model = model or getattr(settings, "OPENAI_MODEL", None) or self.DEFAULT_MODEL

    # -------------------------------------------------------------------------
    # Low-level helpers
    # -------------------------------------------------------------------------
    def _chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """
        Internal sync call. Returns raw text content from the first choice.

        Raises:
            AIUnavailable:      network / auth / rate-limit / timeout
            AIResponseError:    empty or malformed response
        """
        params = {
            "model": self._model,
            "messages": messages,
            "temperature": kwargs.pop("temperature", self.DEFAULT_TEMPERATURE),
            "max_tokens": kwargs.pop("max_tokens", self.DEFAULT_MAX_TOKENS),
            **kwargs,
        }
        try:
            response = self._client.chat.completions.create(**params)
        except (APIConnectionError, APITimeoutError) as e:
            logger.warning("OpenAI request failed: %s", e)
            raise AIUnavailable(f"Provider unreachable: {e}") from e
        except RateLimitError as e:
            logger.warning("OpenAI rate limited: %s", e)
            raise AIUnavailable("Rate limited by provider") from e
        except APIError as e:
            logger.error("OpenAI API error: %s", e)
            raise AIUnavailable(f"Provider error: {e}") from e

        if not response.choices:
            raise AIResponseError("Empty choices list in response")

        content = response.choices[0].message.content
        if not content or not content.strip():
            raise AIResponseError("Empty content in response")

        return content.strip()

    # -------------------------------------------------------------------------
    # Public async-friendly methods (sync body, wrapped by callers)
    # -------------------------------------------------------------------------
    def explain(self, prompt: str) -> str:
        """
        Request a structured explanation from the model.

        Args:
            prompt: Combined system prompt (instructions + engine data) built
                    by ``build_explanation_context``. Instructs the model to
                    output JSON validating against ``AIExplanation``.
        """
        return self._chat([
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Generate the structured JSON response now."},
        ])

    def rewrite(self, prompt: str) -> str:
        """
        Request a structured rewrite from the model.

        Args:
            prompt: Combined system prompt (instructions + engine data) built
                    by ``build_rewrite_context``. Instructs the model to output
                    JSON validating against ``AIRewrite``.
        """
        return self._chat([
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Generate the structured JSON response now."},
        ])