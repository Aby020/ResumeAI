# ResumeAI --- Easy Developer Guide

## 1. What is ResumeAI?

ResumeAI is a Django web application that helps users understand how
well their resume matches a job.

The user can:

1.  Create an account or log in.
2.  Upload a PDF resume.
3.  Optionally add a job description.
4.  Get an ATS score from 0--100.
5.  Get a job-match score when a job description is provided.
6.  See strengths, weaknesses, missing skills, and recommendations.
7.  Optionally receive AI explanations and rewrite suggestions.
8.  Save and revisit previous analyses.

### Important idea

The main scoring system does **not depend on OpenAI**.

The normal analysis is deterministic. OpenAI is an optional extra layer
that explains the results and suggests rewrites based on the results
produced by the ResumeAI engines.

------------------------------------------------------------------------

## 2. Simple Architecture

The easiest way to understand ResumeAI is:

``` text
User
  ↓
Django URL
  ↓
View
  ↓
Analysis Pipeline
  ↓
Read PDF
  ↓
Analyze Resume
  ↓
 ┌───────────────┬────────────────┬─────────────────┐
 ↓               ↓                ↓
ATS Score     Job Match       Resume Statistics
 └───────────────┴────────────────┴─────────────────┘
  ↓
Save Analysis
  ↓
Optional AI Layer
  ↓
Show Results
```

The PDF is parsed once and converted into a `ResumeDocument`.

The ATS engine, job matcher, and statistics use that same analyzed
document instead of repeatedly reading the original PDF.

------------------------------------------------------------------------

## 3. Main Project Folders

``` text
ResumeAI/
│
├── ResumeAI/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── account_manager/
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── core/
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── dashboard/
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── resume/
│   ├── views.py
│   ├── services.py
│   ├── models.py
│   ├── forms.py
│   ├── analyzer.py
│   ├── text_extractor.py
│   ├── ats_engine.py
│   ├── job_matcher.py
│   ├── skills.py
│   ├── utils.py
│   │
│   ├── nlp/
│   │   └── ...
│   │
│   └── ai/
│       └── ...
│
├── templates/
├── static/
├── docs/
├── media/
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

### What each important folder does

  Folder               Simple meaning
  -------------------- ----------------------------------------------
  `ResumeAI/`          Main Django configuration
  `account_manager/`   Login, registration, profile, password reset
  `core/`              Public home page
  `dashboard/`         User dashboard and statistics
  `resume/`            Main ResumeAI functionality
  `resume/nlp/`        Skill, section, entity, and text analysis
  `resume/ai/`         Optional OpenAI integration
  `templates/`         HTML pages
  `static/`            CSS, JavaScript, images
  `docs/`              Technical documentation

------------------------------------------------------------------------

# 4. What Happens When a User Uploads a Resume?

This is the most important workflow to understand.

## Step 1 --- User uploads a PDF

The upload page uses:

``` text
resume/forms.py
```

The main form is:

``` text
ResumeForm
```

It accepts:

-   Resume title
-   PDF resume
-   Optional job description
-   Optional job-description image

------------------------------------------------------------------------

## Step 2 --- Django creates database records

The upload creates:

``` text
Resume
ResumeAnalysis
```

The user is then redirected to the analysis page.

------------------------------------------------------------------------

## Step 3 --- Resume PDF is read

The application reads the uploaded PDF using:

``` text
resume/text_extractor.py
```

The main function is:

``` text
parse_pdf()
```

It extracts:

-   Resume text
-   Number of pages
-   Whether the PDF appears to be scanned

`pdfplumber` is used for PDF extraction.

------------------------------------------------------------------------

## Step 4 --- Resume is analyzed

The extracted text goes to:

``` text
resume/analyzer.py
```

The main function is:

``` text
analyze()
```

It creates a:

``` text
ResumeDocument
```

This document contains the information needed by the rest of the system.

The analysis includes things such as:

-   Sections
-   Skills
-   Degrees
-   Certifications
-   Job titles
-   Companies
-   Experience
-   Action verbs
-   Bullet points
-   Quantified achievements
-   Dates

------------------------------------------------------------------------

# 5. ATS Score

The ATS system is located here:

``` text
resume/ats_engine.py
```

The main function is:

``` text
calculate_ats_score()
```

The final score is between:

``` text
0 and 100
```

## ATS categories

  Category                       Weight
  --------------------------- ---------
  Contact & Links                     5
  Sections & Completeness            10
  Professional Summary                5
  Skills Relevance                   25
  Experience Quality                 20
  Education                          10
  Projects & Certifications          10
  Action Verbs & Language             5
  Keyword Density & Context           5
  Formatting & Structure              5
  **Total**                     **100**

## Grade

``` text
90+  → Excellent
75+  → Good
60+  → Moderate
40+  → Weak
<40  → Poor
```

The system also checks for keyword stuffing. Repeating keywords
excessively can reduce the score.

------------------------------------------------------------------------

# 6. Job Match Score

Job matching is handled by:

``` text
resume/job_matcher.py
```

The main function is:

``` text
calculate_job_fit()
```

It compares the resume with the job description.

## Job-match categories

  Category            Weight
  ---------------- ---------
  Skills                  45
  Experience              20
  Education               10
  Certifications           5
  Title                    5
  Domain                  15
  **Total**          **100**

The system can identify:

-   Matching skills
-   Missing skills
-   Extra skills
-   Required skills
-   Preferred skills
-   Missing experience
-   Education requirements
-   Certification requirements
-   Job title
-   Domain similarity

If there is no job description, the job-match score is:

``` text
None
```

The UI then shows:

``` text
No Job Description
```

------------------------------------------------------------------------

# 7. Skill Matching

ResumeAI uses a canonical skill system.

This is important because people can write the same skill in different
ways.

For example:

``` text
JS        → JavaScript
ML        → Machine Learning
React.js  → React
NodeJS    → Node.js
Python3   → Python
K8s       → Kubernetes
AWS S3    → S3
```

The alias definitions are in:

``` text
resume/nlp/aliases.py
```

Skill extraction is handled by:

``` text
resume/nlp/skill_extractor.py
```

The main canonical skill system is in:

``` text
resume/skills.py
```

This allows ResumeAI to compare skills more accurately.

------------------------------------------------------------------------

# 8. NLP System

The NLP folder is:

``` text
resume/nlp/
```

### `aliases.py`

Converts different spellings into the same standard skill.

### `skill_extractor.py`

Finds skills in resume text.

### `sections.py`

Detects resume sections such as:

-   Summary
-   Skills
-   Experience
-   Education
-   Projects

### `entities.py`

Extracts information such as:

-   Degrees
-   Certifications
-   Job titles
-   Companies
-   Years of experience

### `features.py`

Looks for:

-   Action verbs
-   Bullet points
-   Numbers
-   Achievements
-   Dates

### `normalize.py`

Handles:

-   Tokenization
-   Lemmatization
-   Contact-information redaction

spaCy is used when available. A simpler fallback is available if the
spaCy model is not installed.

------------------------------------------------------------------------

# 9. The Analysis Pipeline

The central pipeline is in:

``` text
resume/services.py
```

The main function is:

``` text
run_analysis_pipeline(pdf_bytes, job_description)
```

In simple terms:

``` text
PDF
 ↓
parse_pdf()
 ↓
analyze()
 ↓
calculate_ats_score()
 ↓
calculate_job_fit()
 ↓
detect_skills()
 ↓
resume_statistics()
 ↓
Create payload
 ↓
Save result
```

The result is stored as a central `payload`.

Important payload sections include:

``` text
_meta
text
is_scanned
page_count
stats
found_skills
missing_skills
ats
job
```

This payload is stored in:

``` text
ResumeAnalysis.resume_json
```

------------------------------------------------------------------------

# 10. Caching

ResumeAI does not want to analyze the same resume repeatedly.

It creates a cache key using:

``` text
SHA1(PDF + Job Description)
```

If the same resume and job description are analyzed again:

``` text
Existing cached result
        ↓
Return result
        ↓
Skip full analysis
```

This makes revisiting an analysis much faster.

The cache logic is mainly in:

``` text
resume/services.py
resume/views.py
```

------------------------------------------------------------------------

# 11. Optional AI Layer

The AI system is located in:

``` text
resume/ai/
```

It is an optional V2 feature.

``` text
ATS + Job Match Results
          ↓
       AIService
          ↓
    OpenAI API
          ↓
 Explanation / Rewrite
```

The AI does **not** replace the ATS or job-match engine.

Instead, it uses their output as the source of truth.

## AI files

### `client.py`

Connects to OpenAI.

Main class:

``` text
OpenAIClient
```

### `prompts.py`

Creates prompts for:

``` text
build_explanation_context()
build_rewrite_context()
```

### `schemas.py`

Validates AI responses using Pydantic.

Important schemas:

``` text
AIExplanation
AIRewrite
ExplanationItem
RewriteSuggestion
```

### `service.py`

Controls the complete AI process:

``` text
Create prompt
 ↓
Call OpenAI
 ↓
Parse response
 ↓
Validate response
 ↓
Check grounding
 ↓
Cache result
 ↓
Return result
```

------------------------------------------------------------------------

# 12. AI Safety / Grounding

ResumeAI checks whether AI-generated information is actually supported
by the analysis.

For example, the AI should not invent a problem that the ATS engine
never detected.

The system checks:

``` text
finding ∈ engine payload
```

For rewrite suggestions:

``` text
target_finding ∈ engine payload
```

and:

``` text
original ∈ resume text
```

If AI output is invalid:

``` text
First attempt
 ↓
Validation fails
 ↓
Retry once with stricter instructions
 ↓
Still invalid?
 ↓
Use deterministic result / hide AI
```

This makes the AI layer safer and more predictable.

------------------------------------------------------------------------

# 13. What Happens If OpenAI Is Not Available?

ResumeAI still works.

If:

``` text
OPENAI_API_KEY
```

is missing:

``` text
ATS works
Job matching works
Recommendations work
AI cards are hidden
```

If OpenAI has:

-   API errors
-   Timeout
-   Rate limit
-   Invalid output

the application falls back to the deterministic system.

So OpenAI is optional.

------------------------------------------------------------------------

# 14. Database Structure

ResumeAI uses Django's built-in:

``` text
User
```

There is no custom user model.

The main relationships are:

``` text
User
 │
 └── many Resume
          │
          └── one ResumeAnalysis
```

## Resume

Stores:

-   User
-   Title
-   PDF file
-   Upload date
-   Deleted status
-   Deleted date

## ResumeAnalysis

Stores:

-   ATS score
-   Job-match score
-   Job description
-   Job image
-   Complete analysis JSON
-   Recommendations
-   Strengths
-   Improvement areas
-   AI explanation
-   AI rewrite
-   AI model
-   AI prompt version
-   Analysis time

------------------------------------------------------------------------

# 15. Soft Delete

ResumeAI does not immediately remove every resume from the history list.

Instead it uses:

``` text
is_deleted
deleted_at
```

History only shows:

``` text
is_deleted=False
```

When a resume is deleted, its stored PDF and job image are also removed
by the delete workflow, and the related analysis is deleted.

------------------------------------------------------------------------

# 16. Authentication

Authentication uses Django's built-in authentication system.

Users can:

-   Register
-   Login
-   Logout
-   View profile
-   Reset password

## Login

The user can log in using:

``` text
Username
OR
Email
```

## Password rules

The registration password requires:

-   Minimum length
-   Uppercase letter
-   Lowercase letter
-   Number
-   Special character

## Security

The project also uses:

-   CSRF protection
-   Django password validation
-   Login-required views
-   User-specific resume queries
-   XFrame protection
-   Template auto-escaping
-   Secrets stored in `.env`

------------------------------------------------------------------------

# 17. Frontend

ResumeAI uses server-rendered Django templates.

There is:

``` text
No Django REST Framework
No React
No Vue
No frontend API calls
```

The browser communicates through normal Django:

``` text
HTML forms
POST requests
Links
```

## Main frontend files

``` text
templates/base.html
templates/dashboard/index.html
templates/resume/upload.html
templates/resume/analysis.html
templates/resume/history.html
static/css/style.css
static/js/main.js
```

Bootstrap 5 and Bootstrap Icons are used.

The UI also supports:

-   Light mode
-   Dark mode
-   Responsive layout
-   Drag-and-drop resume upload
-   Password show/hide
-   Sidebar toggle

------------------------------------------------------------------------

# 18. Main User Journey

The complete user journey is:

``` text
Home
 ↓
Register / Login
 ↓
Dashboard
 ↓
Upload Resume
 ↓
Add optional Job Description
 ↓
Analyze
 ↓
ATS Score
 ↓
Job Match Score
 ↓
Strengths + Improvements
 ↓
Missing Skills
 ↓
Optional AI Explanation
 ↓
Optional AI Rewrite
 ↓
Save Analysis
 ↓
History
```

------------------------------------------------------------------------

# 19. Dashboard

The dashboard shows summary information such as:

-   Average ATS score
-   Highest ATS score
-   Best job match
-   Recent resumes

The dashboard also displays the user's latest resumes.

The implementation is in:

``` text
dashboard/views.py
```

------------------------------------------------------------------------

# 20. Important URLs

  Feature           URL
  ----------------- --------------------------
  Home              `/`
  Login             `/account/login/`
  Register          `/account/register/`
  Profile           `/account/profile/`
  Dashboard         `/dashboard/`
  Upload Resume     `/resume/upload/`
  Resume History    `/resume/history/`
  Resume Analysis   `/resume/analysis/<id>/`
  Delete Resume     `/resume/delete/<id>/`
  Admin             `/admin/`

The exact routing is defined through the root URL configuration and the
individual app URL files.

------------------------------------------------------------------------

# 21. Where to Change Things

This section is useful when you start modifying the project.

  If you want to change...   Edit this
  -------------------------- ---------------------------------------
  ATS scoring                `resume/ats_engine.py`
  ATS weights                `CATEGORY_WEIGHTS`
  Job matching               `resume/job_matcher.py`
  Job-match weights          `MATCH_WEIGHTS`
  Skills                     `resume/skills.py`
  Skill aliases              `resume/nlp/aliases.py`
  Skill extraction           `resume/nlp/skill_extractor.py`
  Resume sections            `resume/nlp/sections.py`
  Entity extraction          `resume/nlp/entities.py`
  Resume features            `resume/nlp/features.py`
  PDF extraction             `resume/text_extractor.py`
  Main analysis object       `resume/analyzer.py`
  Analysis pipeline          `resume/services.py`
  Upload/history/delete      `resume/views.py`
  Database models            `resume/models.py`
  AI prompts                 `resume/ai/prompts.py`
  AI validation              `resume/ai/schemas.py`
  OpenAI client              `resume/ai/client.py`
  AI orchestration           `resume/ai/service.py`
  Login/register             `account_manager/`
  Dashboard                  `dashboard/views.py`
  Home page                  `core/views.py`
  UI                         `templates/` + `static/css/style.css`
  JavaScript                 `static/js/main.js`
  Environment/config         `ResumeAI/settings.py`

------------------------------------------------------------------------

# 22. Environment Variables

Configuration is stored in `.env`.

Important variables include:

``` text
SECRET_KEY
DEBUG
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS

EMAIL_HOST
EMAIL_PORT
EMAIL_USE_TLS
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD

OPENAI_API_KEY
OPENAI_MODEL
DEBUG_AI

DATABASE_URL

CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET

RENDER
```

### Important

Do not put real secrets into GitHub.

The `.env` file is gitignored.

The `.env.example` file should contain variable names, not real secrets.

------------------------------------------------------------------------

# 23. Local Setup

ResumeAI requires:

``` text
Python 3.12
```

Python 3.13 is not supported by the project's spaCy ecosystem according
to the source documentation.

## Install

``` bash
git clone https://github.com/Aby020/ResumeAI.git
cd ResumeAI

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

Optional spaCy model:

``` bash
python -m spacy download en_core_web_sm
```

Create environment file:

``` bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

Then configure the required values.

Run migrations:

``` bash
python manage.py migrate
```

Create admin:

``` bash
python manage.py createsuperuser
```

Start server:

``` bash
python manage.py runserver
```

Open:

``` text
http://127.0.0.1:8000/
```

------------------------------------------------------------------------

# 24. Running Tests

Run:

``` bash
python manage.py test
```

The source documentation reports:

``` text
88 tests passing
```

The tests cover:

-   Skill aliases
-   Skill extraction
-   Section detection
-   Entity extraction
-   Resume analysis
-   ATS scoring
-   Job matching
-   Caching
-   Upload
-   History
-   Delete
-   Authentication
-   Dashboard
-   AI validation
-   AI grounding
-   AI error handling
-   Secret safety

The real OpenAI API is not used by the tests; a fake client is used
instead.

------------------------------------------------------------------------

# 25. Error Handling

ResumeAI is designed to avoid crashing when common problems occur.

## Corrupt PDF

``` text
PDF error
 ↓
Exception handled
 ↓
Error message
 ↓
Redirect to history
```

## Missing PDF

If the original PDF is missing but cached analysis exists:

``` text
Use cached analysis
```

Otherwise:

``` text
Show error
 ↓
Return to history
```

## OpenAI failure

``` text
OpenAI unavailable
 ↓
AI result skipped
 ↓
Normal ATS/job results remain available
```

## No Job Description

``` text
Job Match = None
```

The UI displays:

``` text
No Job Description
```

## Unauthorized access

Users can only access their own resumes.

Trying to access another user's resume results in a 404.

------------------------------------------------------------------------

# 26. Current Implementation Status

## Implemented

The source documentation says these features are implemented:

-   Deterministic ATS engine
-   Job-match engine
-   Skill canonicalization
-   PDF extraction
-   Scanned-PDF detection
-   Single-pass resume analysis
-   Resume upload
-   Resume analysis
-   Resume history
-   Resume deletion
-   Analysis caching
-   AI caching
-   Per-user isolation
-   Registration/login/logout
-   Password reset
-   Password security
-   CSRF/clickjacking/XSS protections
-   Dashboard
-   Optional OpenAI layer
-   AI validation
-   AI grounding
-   AI retry
-   AI graceful degradation
-   88 tests
-   Custom error pages
-   Light/dark theme
-   Responsive UI

------------------------------------------------------------------------

# 27. Optional Features

These features depend on configuration:

### OpenAI

Requires:

``` text
OPENAI_API_KEY
```

Without it, ResumeAI still works.

### SMTP Password Reset

Requires:

``` text
EMAIL_HOST_USER
```

### Cloudinary

Used for production media storage when:

``` text
RENDER
```

is enabled and Cloudinary variables are configured.

### PostgreSQL

Configured using:

``` text
DATABASE_URL
```

Without it, SQLite is used by default.

### spaCy model

Optional:

``` text
en_core_web_sm
```

Without it, the analyzer uses a simpler fallback.

------------------------------------------------------------------------

# 28. Not Yet Implemented

According to the source documentation, these are roadmap items:

-   OCR for scanned PDFs
-   Multi-language resume analysis
-   AI career assistant
-   AI mock interview
-   Docker
-   PWA
-   LinkedIn import

Important:

Scanned PDFs are currently **detected and flagged**, but OCR text
extraction is not implemented.

------------------------------------------------------------------------

# 29. Production Deployment

The documented production platform is Render.

The build process is:

``` bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Start command:

``` bash
gunicorn ResumeAI.wsgi
```

Production configuration includes:

``` text
SECRET_KEY
DEBUG=False
ALLOWED_HOSTS
DATABASE_URL
EMAIL_*
CLOUDINARY_*
RENDER=True
```

------------------------------------------------------------------------

# 30. The Most Important Files to Understand First

If you are new to the project, **do not try to understand every file at
once**.

Follow this order:

### 1. `resume/views.py`

Understand how the user starts an analysis.

### 2. `resume/services.py`

Understand the complete analysis pipeline and caching.

### 3. `resume/text_extractor.py`

Understand how the PDF becomes text.

### 4. `resume/analyzer.py`

Understand how raw text becomes a `ResumeDocument`.

### 5. `resume/ats_engine.py`

Understand how the ATS score is calculated.

### 6. `resume/job_matcher.py`

Understand how the resume is compared with a job description.

### 7. `resume/nlp/`

Understand how skills, sections, entities, and features are extracted.

### 8. `resume/models.py`

Understand what information is stored in the database.

### 9. `resume/ai/`

Understand the optional AI explanation and rewrite system.

### 10. `templates/resume/analysis.html`

Understand how the final analysis is displayed.

------------------------------------------------------------------------

# 31. Simple Mental Model

You can remember the whole application with this:

``` text
UPLOAD
   ↓
READ PDF
   ↓
UNDERSTAND RESUME
   ↓
 ┌───────────────┐
 │               │
 ↓               ↓
ATS SCORE     JOB MATCH
 │               │
 └───────┬───────┘
         ↓
   RECOMMENDATIONS
         ↓
   OPTIONAL OPENAI
         ↓
      SAVE RESULT
         ↓
    SHOW DASHBOARD
```

### In one sentence

**ResumeAI takes a resume, converts it into structured information,
scores it using deterministic ATS and job-matching engines, optionally
asks OpenAI to explain the results, saves everything, and displays the
results through Django templates.**

------------------------------------------------------------------------

# 32. Developer Rule of Thumb

When modifying ResumeAI:

``` text
Want to change scoring?
→ Edit the engine.

Want to change what information is extracted?
→ Edit NLP/analyzer.

Want to change how the pipeline works?
→ Edit services.py.

Want to change AI explanations?
→ Edit resume/ai/.

Want to change what users see?
→ Edit templates/CSS/JS.

Want to change stored data?
→ Edit models + migrations.

Want to change configuration?
→ Edit settings.py + .env.example.
```

This is the easiest way to navigate the project without getting lost.
