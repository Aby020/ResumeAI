# ResumeAI — Backend Architecture

This document describes the ResumeAI V2 analysis backend: how a PDF becomes a
scored, matched, persisted analysis, and where each piece of logic lives. It is
the authoritative reference for contributors working on scoring, NLP, or
performance.

---

## 1. High-level pipeline

```
                       upload_resume (views.py)
                              │
                              ▼
        Resume + ResumeAnalysis rows created (models.py)
                              │
                              ▼
   analyze_resume (views.py) ── read_file_bytes (services.py)
                              │   │
            pdf bytes missing?  │  │  ┌─ cache hit? ──► context_from_payload
                              │  │  │      (resume_json["_meta"].cache_key)
                              ▼  ▼  ▼
              run_analysis_pipeline (services.py)
                              │
         ┌────────────────────┼─────────────────────┐
         ▼                    ▼                     ▼
   text_extractor        ats_engine           job_matcher
   parse_pdf ──► text      calculate_ats_score   calculate_job_fit
         │                    │                     │
         ▼                    ▼                     ▼
   analyzer.analyze ──► ResumeDocument (shared parse, no re-scan)
         │                    │                     │
         └────────────────────┴─────────────────────┘
                              │
                              ▼
              context (template data) + payload (persisted JSON)
                              │
                              ▼
                 analysis.resume_json (cache) + DB scores
```

Key property: **single-pass extraction.** The PDF is parsed once into a
`ResumeDocument`; the ATS scorer and the job matcher both consume that same
object. No stage re-parses or re-scans the raw text.

---

## 2. Resume parsing flow

| Module | Responsibility |
|---|---|
| `resume/text_extractor.py` | `parse_pdf(data) -> {text, has_text, is_scanned, page_count}` via pdfplumber. Sets `is_scanned` when no extractable text layer exists. Wrappers `extract_pdf`, `extract_pdf_text`, `extract_text` preserve legacy callers. |
| `resume/analyzer.py` | `analyze(text, is_scanned, page_count) -> ResumeDocument`. The orchestrator that assembles every derived signal into one structure. |
| `resume/nlp/sections.py` | Segments text into labeled sections (`SECTION_KINDS`: contact, summary, skills, experience, education, projects, certifications, languages, awards, …) using a "short line + header keyword" heuristic. `section_coverage()` reports which standard sections are present. |
| `resume/nlp/entities.py` | Rule + spaCy-NER extraction of degrees (`extract_degrees`), certifications (`extract_certifications`), job titles (`extract_job_titles`), companies (`extract_companies`), and years-of-experience (`extract_years_of_experience`). |
| `resume/nlp/features.py` | Quality signals: action verbs, bullet counts, quantified achievements (`extract_quantified_achievements`), date ranges and years worked, date-format consistency. |
| `resume/nlp/normalize.py` | Tokenization, contact redaction, and spaCy lemmatization with a plain-token fallback when the model is absent. |
| `resume/nlp/skill_extractor.py` | The single canonical skill extractor — resolves aliases, assigns categories, dedupes. |

`ResumeDocument` fields (dataclass in `analyzer.py`):

```text
text, word_count, character_count, is_scanned, page_count,
sections (list), coverage (dict), skills (dict),
canonical_skills (set), entities (dict), features (dict), contact (dict)
```

`to_dict()` makes it JSON-serializable for the `resume_json` cache.

### Canonicalization (before any comparison)

`resume/nlp/aliases.py` defines an alias graph so equivalent spellings collapse
to one canonical skill **before** scoring or matching:

```
JS      ↔ JavaScript        React.js  ↔ React
NodeJS  ↔ Node.js           Python3   ↔ Python
ML      ↔ Machine Learning  AI        ↔ Artificial Intelligence
C++     ↔ cpp               K8s       ↔ Kubernetes
AWS S3  ↔ S3                ...
```

`resume/skills.py` is the single source of truth taxonomy — `SKILL_CATEGORIES`
(expanded beyond the original ~70) plus per-category relevance weights. The old
duplicate detectors (`detect_resume_skills`, `detect_skills`,
`extract_job_skills`) were consolidated; `utils.detect_skills` is now a thin
wrapper over the canonical extractor.

---

## 3. ATS scoring pipeline

`resume/ats_engine.py` — `calculate_ats_score(text, doc=None)` returns:

```text
ats_score, grade, breakdown{category: {score, max}}, strengths,
improvements, recommendations, detected_skills
```

The public contract is unchanged from V1, but the internals are a **weighted
rubric that evaluates content, not keyword presence.** A resume that merely
contains the words "experience" or "education" no longer scores points.

### Rubric (sums to 100)

| Category | Weight | What earns points |
|---|---|---|
| Contact & Links | 5 | email, phone, LinkedIn, GitHub/portfolio — **partial credit per item** |
| Sections & Completeness | 10 | which standard sections are present, weighted |
| Professional Summary | 5 | present + 40–120 words + quality signals |
| Skills Relevance | 25 | canonical count (log-scaled), tech-vs-soft weighting, synonym-aware; blended with JD relevance when a JD is given |
| Experience Quality | 20 | section present + quantified years + action verbs + quantified achievements + titles/companies detected |
| Education | 10 | section + degree level + field of study |
| Projects & Certifications | 10 | projects with tech used + recognized certifications |
| Action Verbs & Language | 5 | strong-action-verb ratio in experience/project lines |
| Keyword Density & Context | 5 | **balanced** density; repetition ratio `(mentions - unique)/unique` — stuffing is penalized |
| Formatting & Structure | 5 | section headers, bullets, consistent dates, 250–1000 words |

Calibration (verified by tests): an empty/garbage resume scores **<25**; a
keyword-dump scores ~8 (previously ~72); a genuine strong resume scores 80+.
Grade thresholds follow the new distribution.

---

## 4. Job matching flow

`resume/job_matcher.py` — `calculate_job_fit(resume_skills, job_description, doc=None)`.

### Step 1 — Parse the job description

`extract_job_requirements(job_description)` returns:

```text
required_skills, preferred_skills, years, degrees, certifications, title
```

Required vs preferred is decided by marker presence, with required winning on
ties (a skill listed in both sections is treated as required).

### Step 2 — Weighted composite

`MATCH_WEIGHTS` (sums to 100):

| Dimension | Weight | Evaluates |
|---|---|---|
| skills | 45 | canonical overlap — required skills weighted over preferred |
| experience | 20 | JD-required years vs resume years |
| education | 10 | JD degree requirement vs highest resume degree |
| certifications | 5 | JD-listed certs vs resume certs |
| title | 5 | JD role vs resume job titles (lemmatized token similarity) |
| domain | 15 | responsibility/industry keyword coverage (de-skilled tokens) |

### Step 3 — Return value

Backward-compatible keys plus richer detail:

```text
job_fit_score, matching_skills, missing_skills, extra_skills,
recommendations,                     # ← V1 keys
match_confidence, strong_matches,
missing_required_skills, missing_preferred_skills,
missing_experience, missing_certifications, missing_technologies,
resume_strengths, resume_weaknesses, suggestions
```

The score is **stable independent of JD length** — it is a weighted composite,
not a raw set ratio. With no JD supplied, `job_fit_score` is `None` and the
view hides the job-match block.

---

## 5. Service layer

`resume/services.py` is the thin-views boundary. Views call one function and
get back ready-to-render data; no scoring constants or hashing live in views.

| Function | Purpose |
|---|---|
| `read_file_bytes(file_obj)` | Safely reads a `FileField`'s bytes; returns `None` (logged) when the file is missing/corrupt so callers can degrade gracefully. |
| `build_cache_key(pdf_bytes, job_description)` | `sha1(pdf_bytes + job_description)` — the cache identity. |
| `run_analysis_pipeline(pdf_bytes, job_description)` | Runs the full pipeline in one pass; returns `(context, payload)`. |
| `context_from_payload(payload)` | Rebuilds the render context from a stored `resume_json` payload (cache-hit path). |
| `_build_context(payload)` | Shared builder: payload → the dict of template variables (`ats_score`, `grade`, `ats_breakdown`, `matching_skills`, `job_recommendations`, …). |

### Caching

`ResumeAnalysis.resume_json` (JSONField) is the analysis cache. The payload
includes `_meta.cache_key` and `_meta.version` (`CACHE_VERSION = 1`). On every
`analyze_resume` GET:

1. Read bytes; if the file is missing, render the last cached analysis or
   explain + redirect to re-upload.
2. Recompute the cache key from the current bytes + JD.
3. If it matches the stored key → render straight from `resume_json`
   (**no re-parse, no re-score**).
4. Otherwise run the pipeline once and persist.

Bump `CACHE_VERSION` when scoring logic changes enough that stale results
should be discarded.

---

## 6. Utility modules

| Module | Contents |
|---|---|
| `resume/utils.py` | `detect_skills` (canonical wrapper), `resume_statistics` (word/char counts, contact flags). |
| `resume/nlp/normalize.py` | `normalize_text`, `redact_contact` (email/URL/phone → placeholders), `tokenize`, `lemmatize`. `_get_nlp()` lazily loads `en_core_web_sm` once per process and **falls back to plain tokenization if spaCy or the model is absent** — the app never crashes on a fresh clone without the model. |
| `resume/nlp/features.py` | Date-range regexes use horizontal-only whitespace (`[^\S\n]*`) so spans never cross lines; `_YEAR_RE` is non-capturing to avoid `findall` returning partial years. |
| `resume/nlp/entities.py` | Two-letter degrees (`B.S`, `M.E`) match only uppercase/dotted to avoid "give me" → M.E; job-title regexes require whole-word edges to avoid "engineers" → Engineer. |

---

## 7. Data model

| Model | Fields (relevant) |
|---|---|
| `Resume` | `user` (FK), `title`, `file` (FileField → `resumes/`), `uploaded_at`, `is_deleted`, `deleted_at` |
| `ResumeAnalysis` (OneToOne) | `ats_score`, `job_match_score`, `job_description`, `job_image` (→ `job_descriptions/`), `resume_json` (JSONField cache), `recommendations`, `strengths`, `improvement_areas`, `analyzed_at` |

Deletion uses the storage API (`storage.exists` / `storage.delete`) so it works
identically for local disk and Cloudinary.

---

## 8. Performance notes

- spaCy model loads lazily and is cached module-wide (cold start ~4.6 s, then
  reused across requests); NER is disabled for the lemmatization pass.
- `dashboard/views.py` issues **one** query: `select_related("analysis")` plus a
  single `aggregate()` for avg/highest/best stats (verified ≤6 queries by test).
- The `resume_json` cache short-circuits analysis on reload.
- All analysis logic is unit-tested against synthetic PDFs (`make_pdf` in
  `resume/tests.py`).

## 9. Test layout

`resume/tests.py` (~78 tests) covers aliases, taxonomy, sections, entities,
features, the analyzer document, ATS rubric calibration, job-match composite,
the service/cache layer, and view integration (cache hit, corrupt/missing PDF,
delete, dashboard query count). `account_manager/tests.py`, `dashboard/tests.py`
and `core/tests.py` cover the auth, dashboard and landing-page integration
flows. Run everything with:

```bash
python manage.py test
```
