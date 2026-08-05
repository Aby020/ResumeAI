"""
Text normalization utilities.

Provides clean tokenization and optional spaCy lemmatization with a graceful
fallback so the rest of the pipeline never depends on a model being present.
"""
import re

_WS_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,16}")
_TOKEN_RE = re.compile(r"[^A-Za-z0-9]+")

_nlp = None


def _get_nlp():
    """Lazily load the spaCy model; return None if unavailable."""
    global _nlp
    if _nlp is None:
        try:
            import spacy

            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = False
    return _nlp or None


def normalize_text(text):
    """Collapse whitespace and strip."""
    if not text:
        return ""
    return _WS_RE.sub(" ", text).strip()


def redact_contact(text):
    """Replace emails, URLs and phone numbers so they don't pollute matching."""
    if not text:
        return ""
    text = _EMAIL_RE.sub(" [email] ", text)
    text = _URL_RE.sub(" [url] ", text)
    text = _PHONE_RE.sub(" [phone] ", text)
    return normalize_text(text)


def tokenize(text):
    """Split into lowercase alphanumeric tokens."""
    if not text:
        return []
    return [t.lower() for t in _TOKEN_RE.split(text) if t]


def lemmatize(text):
    """
    spaCy lemmatization with a plain-token fallback.

    NER is disabled for this pass: lemmatization only needs tokenizer + POS,
    so running the full pipeline (incl. NER) would be wasted work. The loaded
    model instance is cached module-wide and reused across calls.
    """
    nlp = _get_nlp()
    if nlp is None:
        return " ".join(tokenize(text))
    return " ".join(tok.lemma_.lower() for tok in nlp(text, disable=["ner"]))
