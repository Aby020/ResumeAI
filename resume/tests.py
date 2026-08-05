"""
Test suite for the ResumeAI analysis backend.

Covers the NLP foundation (canonicalization, extraction) first; later phases
add parsing, ATS scoring, job matching and performance tests.
"""
import json
import os
import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from resume.models import Resume, ResumeAnalysis
from resume.services import build_cache_key, context_from_payload, run_analysis_pipeline
from resume.text_extractor import parse_pdf


def make_pdf(text="Python and JavaScript"):
    """Generate a minimal single-page PDF that pdfplumber can parse."""
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += (
        b"trailer\n<< /Size %d /Root 1 0 R >>\n"
        b"startxref\n%d\n%%%%EOF" % (len(objects) + 1, xref_pos)
    )
    return bytes(out)

from resume.analyzer import analyze
from resume.ats_engine import CATEGORY_WEIGHTS, calculate_ats_score, detect_resume_skills
from resume.job_matcher import (
    MATCH_WEIGHTS,
    calculate_job_fit,
    extract_job_requirements,
    extract_job_skills,
    extract_job_years,
)
from resume.nlp import features, sections
from resume.nlp.entities import (
    extract_certifications,
    extract_companies,
    extract_degrees,
    extract_entities,
    extract_job_titles,
    extract_years_of_experience,
)
from resume.nlp.skill_extractor import canonical_skills, extract_skills
from resume.utils import detect_skills


class CanonicalizationTests(SimpleTestCase):
    """Alias resolution: variants must map to one canonical name."""

    def test_python3_equals_python(self):
        self.assertEqual(canonical_skills("I use Python3 and Python"), ["Python"])

    def test_js_equals_javascript(self):
        self.assertEqual(canonical_skills("JS with JavaScript"), ["JavaScript"])

    def test_react_js_equals_react(self):
        self.assertEqual(
            canonical_skills("React.js / Reactjs / React"),
            ["React"],
        )

    def test_nodejs_equals_node_js(self):
        self.assertEqual(
            canonical_skills("NodeJS, Node.js, Node"),
            ["Node.js"],
        )

    def test_ml_equals_machine_learning(self):
        self.assertEqual(
            canonical_skills("ML and machine learning"),
            ["Machine Learning"],
        )

    def test_ai_equals_artificial_intelligence(self):
        self.assertEqual(
            canonical_skills("AI and Artificial Intelligence"),
            ["Artificial Intelligence"],
        )

    def test_cpp_variants(self):
        self.assertEqual(canonical_skills("cpp, C++, cplusplus"), ["C++"])

    def test_k8s_equals_kubernetes(self):
        self.assertEqual(canonical_skills("k8s and kubernetes"), ["Kubernetes"])

    def test_typescript_shorthand(self):
        self.assertEqual(canonical_skills("ts and typescript"), ["TypeScript"])


class SkillExtractionTests(SimpleTestCase):
    """Canonical extraction precision and recall."""

    def test_expanded_taxonomy_detects_real_world_skills(self):
        result = canonical_skills("Kafka Terraform Snowflake Flutter")
        self.assertEqual(
            result,
            ["Flutter", "Kafka", "Snowflake", "Terraform"],
        )

    def test_no_single_letter_false_positives(self):
        # Bullet marker "C.", English "go", "R&D" must NOT match C/R/Go.
        text = (
            "We built the system. Good job everyone. "
            "The C. Wright building is on the list. Research and development."
        )
        result = canonical_skills(text)
        self.assertNotIn("C", result)
        self.assertNotIn("R", result)
        self.assertNotIn("Go", result)

    def test_cpp_does_not_imply_c(self):
        self.assertEqual(canonical_skills("C++ and C#"), ["C#", "C++"])

    def test_counts_reflect_occurrences(self):
        skills = {s["name"]: s["count"] for s in extract_skills(
            "Python Python python and SQL and python"
        )}
        self.assertEqual(skills["Python"], 4)
        self.assertEqual(skills["SQL"], 1)

    def test_skill_has_category_and_weight(self):
        skills = extract_skills("Django and Communication")
        by_name = {s["name"]: s for s in skills}
        self.assertEqual(by_name["Django"]["category"], "Backend & Frameworks")
        self.assertEqual(by_name["Django"]["weight"], 1.0)
        self.assertEqual(by_name["Communication"]["category"], "Soft Skills")
        self.assertEqual(by_name["Communication"]["weight"], 0.4)

    def test_skill_inside_compound_word_not_detected(self):
        # "postgresql" contains "sql" but must not count as standalone SQL.
        result = canonical_skills("Experience with PostgreSQL")
        self.assertNotIn("SQL", result)
        self.assertIn("PostgreSQL", result)

    def test_empty_and_none_input(self):
        self.assertEqual(canonical_skills(""), [])
        self.assertEqual(canonical_skills(None), [])


class DetectorUnificationTests(SimpleTestCase):
    """All three historical detectors now agree on the canonical vocabulary."""

    def test_all_detectors_agree(self):
        text = "JS, Python3, React.js and ML"
        self.assertEqual(
            detect_resume_skills(text),
            canonical_skills(text),
        )
        self.assertEqual(
            extract_job_skills(text),
            canonical_skills(text),
        )

    def test_detect_skills_returns_found_and_missing_pair(self):
        found, missing = detect_skills("Python and React")
        self.assertIsInstance(found, list)
        self.assertIsInstance(missing, list)
        self.assertIn("Python", found)
        self.assertIn("React", found)
        self.assertTrue(all(isinstance(s, str) for s in missing))


class SectionDetectionTests(SimpleTestCase):
    """Section segmentation: header detection and content capture."""

    SAMPLE = (
        "John Doe\n"
        "john@example.com\n"
        "\n"
        "Professional Summary\n"
        "Engineer with 5+ years of experience.\n"
        "\n"
        "Skills\n"
        "Python, JavaScript, React, SQL\n"
        "\n"
        "Work Experience\n"
        "Senior Software Engineer, Acme Inc\n"
        "2019 - 2021\n"
        "Built a pipeline.\n"
        "\n"
        "Education\n"
        "B.S. Computer Science, State University\n"
    )

    def test_detect_sections_orders_in_document(self):
        kinds = [s["kind"] for s in sections.detect_sections(self.SAMPLE)]
        self.assertEqual(
            kinds[:5],
            ["summary", "skills", "experience", "education"],
        )

    def test_experience_section_captures_its_content(self):
        content = sections.get_section(self.SAMPLE, "experience")
        self.assertIn("Senior Software Engineer, Acme Inc", content)
        self.assertIn("Built a pipeline.", content)
        self.assertNotIn("Python, JavaScript", content)

    def test_long_sentence_is_not_a_header(self):
        # "5+ years of experience" appears in prose, not as a header.
        text = "Engineer with 5+ years of experience building tools."
        self.assertIsNone(sections.get_section(text, "experience"))

    def test_section_coverage_flags_present_and_absent(self):
        coverage = sections.section_coverage(self.SAMPLE)
        self.assertTrue(coverage["experience"])
        self.assertTrue(coverage["education"])
        self.assertFalse(coverage["projects"])
        self.assertFalse(coverage["certifications"])


class FeatureDetectionTests(SimpleTestCase):
    """Structural and language-quality signals."""

    def test_action_verbs_counted(self):
        text = "I built a system, optimized the pipeline, and led the team."
        self.assertEqual(features.count_action_verbs(text), 3)

    def test_bullets_detected(self):
        text = "- First bullet\n• Second bullet\n1. Third bullet\nplain line"
        self.assertEqual(features.count_bullets(text), 3)

    def test_quantified_achievements(self):
        text = "- Cut costs by 20%\n- Led a team\n- Grew revenue by $1.2M"
        result = features.extract_quantified_achievements(text)
        self.assertEqual(len(result), 2)
        self.assertIn("Cut costs by 20%", result)

    def test_date_ranges_and_present(self):
        ranges = features.extract_date_ranges("2019 - 2021 and Jan 2018 - Present")
        pairs = {(r["start"], r["end"].lower()) for r in ranges}
        self.assertEqual(len(ranges), 2)
        self.assertIn(("2019", "2021"), pairs)
        self.assertIn(("Jan 2018", "present"), pairs)

    def test_mixed_date_formats_inconsistent(self):
        text = "2019 - 2021\nJan 2018 - Present"
        self.assertFalse(features.consistent_dates(text))

    def test_consistent_year_only_dates(self):
        text = "2019 - 2021\n2021 - 2023"
        self.assertTrue(features.consistent_dates(text))


class EntityExtractionTests(SimpleTestCase):
    """Degrees, certifications, titles, companies, years-of-experience."""

    def test_degrees(self):
        result = extract_degrees(
            "B.S. in CS, M.Tech, and an MBA (PhD coursework done)"
        )
        self.assertIn("B.S", result)
        self.assertIn("M.Tech", result)
        self.assertIn("MBA", result)
        self.assertIn("PhD", result)

    def test_certifications(self):
        result = extract_certifications(
            "AWS Certified Solutions Architect, Certified Scrum Master, PMP"
        )
        self.assertIn("AWS Certified", result)
        self.assertIn("Scrum Master", result)
        self.assertIn("PMP", result)

    def test_job_titles(self):
        result = extract_job_titles(
            "Senior Software Engineer at Acme\n"
            "Data Scientist at Beta\n"
            "Worked as a Full Stack Developer"
        )
        self.assertIn("Senior Software Engineer", result)
        self.assertIn("Data Scientist", result)

    def test_no_degree_false_positives_in_english_words(self):
        # "me"/"be"/"bs" as ordinary words, "github.com", "Came" must not
        # produce degree matches.
        result = extract_degrees(
            "Please give me the code. It would be great. github.com/jane Came late."
        )
        self.assertEqual(result, [])

    def test_uppercase_or_dotted_degree_abbreviations(self):
        self.assertIn("M.E", extract_degrees("M.E degree at UNAM"))
        self.assertIn("B.S", extract_degrees("B.S. in Computer Science"))
        self.assertIn("MBA", extract_degrees("earned an MBA in 2020"))

    def test_no_engineer_title_from_engineers(self):
        result = extract_job_titles("Led a team of 4 engineers")
        self.assertNotIn("Engineer", result)

    def test_company_ner_does_not_return_skill_words(self):
        result = extract_companies(
            "Senior Engineer at Acme Inc using JavaScript, SQL and AWS"
        )
        for noise in ("JavaScript", "SQL", "AWS"):
            self.assertNotIn(noise, result)
        self.assertIn("Acme Inc", result)

    def test_years_of_experience(self):
        self.assertEqual(
            extract_years_of_experience("I have 6+ years of experience"),
            6,
        )
        self.assertEqual(
            extract_years_of_experience("5 to 8 years in data engineering"),
            8,
        )
        self.assertIsNone(extract_years_of_experience("no experience stated"))

    def test_extract_entities_bundle(self):
        result = extract_entities(
            "Work Experience\n"
            "Senior Software Engineer at Acme Inc\n"
            "5+ years of experience\n"
            "AWS Certified Solutions Architect, MBA"
        )
        self.assertIn("Senior Software Engineer", result["job_titles"])
        self.assertEqual(result["years_of_experience"], 5)
        self.assertIn("AWS Certified", result["certifications"])
        self.assertIn("MBA", result["degrees"])


class AnalyzerTests(SimpleTestCase):
    """The single-pass ResumeDocument pipeline."""

    SAMPLE = (
        "Jane Smith\n"
        "jane@example.com • +1 555 123 4567\n"
        "linkedin.com/in/jane\n"
        "\n"
        "Professional Summary\n"
        "Engineer with 5+ years of experience.\n"
        "\n"
        "Skills\n"
        "Python, JavaScript, React, SQL\n"
        "\n"
        "Work Experience\n"
        "Senior Software Engineer, Acme Inc\n"
        "2019 - Present\n"
        "- Built a pipeline, cutting costs by 20%\n"
        "- Led a team of 4 engineers\n"
        "\n"
        "Education\n"
        "B.S. Computer Science\n"
    )

    def test_analyze_builds_complete_document(self):
        doc = analyze(self.SAMPLE)
        self.assertIsInstance(doc.word_count, int)
        self.assertGreater(doc.word_count, 30)
        self.assertTrue(doc.has_email)
        self.assertTrue(doc.has_phone)
        self.assertTrue(doc.has_linkedin)
        self.assertFalse(doc.has_github)

    def test_analyze_canonical_skills(self):
        doc = analyze("Python3 and JS are my main languages")
        self.assertEqual(doc.canonical_skills, ["JavaScript", "Python"])

    def test_analyze_sections_and_features(self):
        doc = analyze(self.SAMPLE)
        self.assertTrue(doc.coverage["experience"])
        self.assertTrue(doc.coverage["education"])
        self.assertGreaterEqual(doc.features["action_verb_count"], 1)
        self.assertGreaterEqual(doc.features["bullet_count"], 2)
        self.assertGreaterEqual(doc.features["quantified_achievements"], 1)

    def test_analyze_entities(self):
        doc = analyze(self.SAMPLE)
        self.assertEqual(doc.entities["years_of_experience"], 5)
        self.assertIn("Senior Software Engineer", doc.entities["job_titles"])

    def test_analyze_empty_and_none(self):
        for raw in ("", None):
            doc = analyze(raw)
            self.assertEqual(doc.word_count, 0)
            self.assertEqual(doc.canonical_skills, [])
            self.assertFalse(doc.has_email)

    def test_to_dict_is_serializable(self):
        payload = analyze(self.SAMPLE).to_dict()
        self.assertIsInstance(payload, dict)
        self.assertIn("sections", payload)
        self.assertIn("features", payload)
        self.assertIn("canonical_skills", payload)


class ATSScoringTests(SimpleTestCase):
    """The weighted rubric replaces the old presence-based checklist."""

    STRONG = (
        "Jane Smith\n"
        "jane@example.com | +1 555 123 4567\n"
        "linkedin.com/in/jane | github.com/jane\n"
        "\n"
        "Professional Summary\n"
        "Data engineer with 6+ years of experience building scalable data "
        "pipelines. Expert in Python, SQL, AWS and Docker with a strong "
        "focus on performance and reliability.\n"
        "\n"
        "Technical Skills\n"
        "Python, JavaScript, React, SQL, PostgreSQL, Redis, AWS, Docker, "
        "Kubernetes, Git, Linux, CI/CD\n"
        "\n"
        "Work Experience\n"
        "Senior Data Engineer, Acme Inc\n"
        "Jan 2019 - Present\n"
        "- Built a data pipeline that cut operating costs by 20 percent\n"
        "- Led a team of 4 engineers and improved delivery speed\n"
        "- Optimized database queries, reducing latency by 30 percent\n"
        "- Deployed services to AWS and managed Kubernetes clusters\n"
        "\n"
        "Data Analyst, Beta Corp\n"
        "Jan 2017 - Dec 2018\n"
        "- Analyzed sales data and increased revenue by 15 percent\n"
        "- Created Tableau dashboards for the executive team\n"
        "\n"
        "Education\n"
        "B.S. in Computer Science, State University\n"
        "\n"
        "Projects\n"
        "- ETL pipeline in Python processing 1M rows daily\n"
        "\n"
        "Certifications\n"
        "AWS Certified Solutions Architect\n"
    )

    def test_empty_resume_scores_low(self):
        result = calculate_ats_score("")
        self.assertLess(result["ats_score"], 25)
        self.assertEqual(result["grade"], "Poor")

    def test_keyword_dump_is_not_rewarded(self):
        # This exact input scored 72/100 under the old presence-based rubric.
        result = calculate_ats_score(
            "summary experience education project\n"
            "john@example.com 555-123-4567"
        )
        self.assertLess(result["ats_score"], 50)

    def test_thin_formatted_resume_scores_mid_range(self):
        thin = (
            "John Doe\njohn@example.com\n\n"
            "Professional Summary\nI am a developer with some experience.\n\n"
            "Skills\nPython\n\n"
            "Work Experience\nSoftware Developer, Company\n\n"
            "Education\nState University\n\n"
            "Projects\nBuilt a website"
        )
        result = calculate_ats_score(thin)
        self.assertGreaterEqual(result["ats_score"], 25)
        self.assertLess(result["ats_score"], 60)

    def test_strong_resume_scores_high(self):
        result = calculate_ats_score(self.STRONG)
        self.assertGreaterEqual(result["ats_score"], 80)
        self.assertIn(result["grade"], ("Good", "Excellent"))

    def test_canonical_skills_are_equivalent_in_scoring(self):
        a = calculate_ats_score("Python3 and JS are my core languages")
        b = calculate_ats_score("Python and JavaScript are my core languages")
        self.assertEqual(
            a["breakdown"]["Skills Relevance"]["score"],
            b["breakdown"]["Skills Relevance"]["score"],
        )
        self.assertEqual(a["detected_skills"], b["detected_skills"])

    def test_keyword_stuffing_is_penalized(self):
        result = calculate_ats_score(
            "Professional Summary\n"
            "Python Python Python Python Python Python Python\n"
            "Skills\nPython"
        )
        self.assertLessEqual(
            result["breakdown"]["Keyword Density & Context"]["score"], 2
        )

    def test_breakdown_covers_full_rubric(self):
        result = calculate_ats_score(self.STRONG)
        self.assertEqual(
            set(result["breakdown"]),
            set(CATEGORY_WEIGHTS),
        )
        for category, detail in result["breakdown"].items():
            self.assertIn("score", detail)
            self.assertIn("max", detail)
            self.assertLessEqual(detail["score"], detail["max"])
        self.assertEqual(sum(CATEGORY_WEIGHTS.values()), 100)

    def test_partial_contact_credit(self):
        result = calculate_ats_score("jane@example.com\nMy resume.")
        self.assertEqual(
            result["breakdown"]["Contact & Links"]["score"], 2
        )

    def test_detected_skills_are_canonical(self):
        result = calculate_ats_score(self.STRONG)
        self.assertIn("Python", result["detected_skills"])
        self.assertIn("JavaScript", result["detected_skills"])
        self.assertNotIn("JS", result["detected_skills"])
        self.assertNotIn("Python3", result["detected_skills"])

    def test_detected_skills_flat_list_for_job_matching(self):
        result = calculate_ats_score(self.STRONG)
        self.assertTrue(
            all(isinstance(s, str) for s in result["detected_skills"])
        )


class JobMatchingTests(SimpleTestCase):
    """Weighted composite matching against extracted job requirements."""

    JD = (
        "Senior Software Engineer - Backend\n"
        "\n"
        "Looking for a Senior Software Engineer with 5+ years of experience "
        "to build scalable systems.\n"
        "\n"
        "Requirements:\n"
        "- Python and JavaScript\n"
        "- React and Node.js\n"
        "- SQL and PostgreSQL\n"
        "- AWS and Docker\n"
        "- Bachelor's degree in Computer Science\n"
        "\n"
        "Preferred:\n"
        "- Go\n"
        "- GraphQL\n"
        "- AWS Certified Solutions Architect\n"
    )

    STRONG = (
        "Professional Summary\n"
        "Backend engineer with 6+ years of experience building scalable systems.\n"
        "\n"
        "Skills\n"
        "Python, JavaScript, React, Node.js, SQL, PostgreSQL, AWS, Docker, Go, GraphQL\n"
        "\n"
        "Work Experience\n"
        "Senior Software Engineer, Acme Inc\n"
        "Jan 2019 - Present\n"
        "- Built and deployed services on AWS using Docker\n"
        "- Developed React frontends backed by Node.js and PostgreSQL\n"
        "\n"
        "Education\n"
        "B.S. Computer Science\n"
        "\n"
        "Certifications\n"
        "AWS Certified Solutions Architect\n"
    )

    def test_extract_job_requirements_splits_required_preferred(self):
        requirements = extract_job_requirements(self.JD)
        self.assertIn("Python", requirements["required_skills"])
        self.assertIn("Docker", requirements["required_skills"])
        self.assertIn("Go", requirements["preferred_skills"])
        self.assertIn("GraphQL", requirements["preferred_skills"])
        self.assertEqual(requirements["years"], 5)
        self.assertIn("Bachelor's", requirements["degrees"])

    def test_extract_job_years_handles_forms(self):
        self.assertEqual(extract_job_years("5+ years of experience"), 5)
        self.assertEqual(extract_job_years("5 to 7 years experience"), 7)
        self.assertEqual(extract_job_years("minimum 8 years"), 8)
        self.assertIsNone(extract_job_years("no time requirement stated"))

    def test_full_match_scores_high(self):
        doc = analyze(self.STRONG)
        result = calculate_job_fit(doc.canonical_skills, self.JD, doc=doc)
        self.assertGreaterEqual(result["job_fit_score"], 85)
        self.assertGreaterEqual(result["match_confidence"], 80)
        self.assertEqual(result["missing_required_skills"], [])
        self.assertEqual(result["missing_experience"], [])

    def test_partial_match_surfaces_gaps(self):
        weak = analyze(
            "Professional Summary\nJunior developer with 2 years of experience.\n"
            "\nSkills\nPython, SQL\n\n"
            "Work Experience\nSoftware Developer\n2022 - 2024\n- Wrote Python scripts\n"
            "\nEducation\nHigh School"
        )
        result = calculate_job_fit(weak.canonical_skills, self.JD, doc=weak)
        self.assertIn("React", result["missing_required_skills"])
        self.assertIn("Docker", result["missing_required_skills"])
        self.assertTrue(result["missing_experience"])
        self.assertIn("AWS Certified", result["missing_certifications"])
        self.assertLess(result["job_fit_score"], 50)

    def test_canonical_aliases_resolve_in_matching(self):
        doc = analyze("Skills\nJavaScript, Python, Machine Learning")
        result = calculate_job_fit(
            doc.canonical_skills,
            "We need JS, Python3 and ML experts.",
            doc=doc,
        )
        self.assertEqual(
            set(result["matching_skills"]),
            {"JavaScript", "Python", "Machine Learning"},
        )
        self.assertEqual(result["missing_skills"], [])

    def test_no_job_description_returns_none(self):
        result = calculate_job_fit(["Python"], "")
        self.assertIsNone(result["job_fit_score"])
        self.assertEqual(result["recommendations"], ["No job description provided."])

    def test_backward_compatible_keys_present(self):
        doc = analyze(self.STRONG)
        result = calculate_job_fit(doc.canonical_skills, self.JD, doc=doc)
        for key in (
            "job_fit_score",
            "matching_skills",
            "missing_skills",
            "extra_skills",
            "recommendations",
        ):
            self.assertIn(key, result)

    def test_skills_only_call_without_doc(self):
        result = calculate_job_fit(["Python", "SQL"], self.JD)
        self.assertIsInstance(result["job_fit_score"], int)
        self.assertIn("Python", result["matching_skills"])

    def test_missing_technologies_excludes_soft_skills(self):
        doc = analyze("Skills\nPython")
        result = calculate_job_fit(
            doc.canonical_skills,
            "Requires Python and Communication skills.",
            doc=doc,
        )
        self.assertNotIn("Communication", result["missing_technologies"])

    def test_education_shortfall_flagged(self):
        doc = analyze(
            "Skills\nPython\n\nEducation\nB.S. Computer Science"
        )
        result = calculate_job_fit(
            doc.canonical_skills,
            "PhD in Computer Science required. Must know Python.",
            doc=doc,
        )
        self.assertTrue(
            any("education" in w.lower() for w in result["resume_weaknesses"])
        )
        self.assertTrue(any("education" in s.lower() for s in result["suggestions"]))

    def test_match_weights_sum_to_100(self):
        self.assertEqual(sum(MATCH_WEIGHTS.values()), 100)

    def test_extract_job_skills_still_canonical(self):
        self.assertEqual(
            extract_job_skills("JS and Python3"),
            ["JavaScript", "Python"],
        )


class AnalysisServiceTests(SimpleTestCase):
    """Caching + single-pass pipeline helpers (no DB)."""

    def test_parse_pdf_extracts_text_and_flags(self):
        result = parse_pdf(make_pdf("Hello Resume"))
        self.assertEqual(result["text"], "Hello Resume")
        self.assertTrue(result["has_text"])
        self.assertFalse(result["is_scanned"])
        self.assertEqual(result["page_count"], 1)

    def test_corrupt_pdf_raises(self):
        with self.assertRaises(Exception):
            parse_pdf(b"this is not a pdf")

    def test_build_cache_key_is_deterministic_and_input_sensitive(self):
        pdf = make_pdf()
        self.assertEqual(
            build_cache_key(pdf, "JD A"),
            build_cache_key(pdf, "JD A"),
        )
        self.assertNotEqual(
            build_cache_key(pdf, "JD A"),
            build_cache_key(pdf, "JD B"),
        )
        self.assertNotEqual(
            build_cache_key(pdf, "JD A"),
            build_cache_key(make_pdf("other"), "JD A"),
        )

    def test_run_analysis_pipeline_payload_is_json_serializable(self):
        _, payload = run_analysis_pipeline(make_pdf(), "Needs JS and Python3")
        json.dumps(payload)  # must not raise
        self.assertIn("cache_key", payload["_meta"])
        self.assertEqual(payload["_meta"]["version"], 1)
        self.assertIn("ats_score", payload["ats"])
        self.assertIn("job_fit_score", payload["job"])

    def test_context_from_payload_has_all_template_keys(self):
        _, payload = run_analysis_pipeline(make_pdf(), "Needs JS and Python3")
        context = context_from_payload(payload)
        for key in (
            "text", "word_count", "character_count", "found_skills",
            "missing_skills", "ats_score", "grade", "ats_breakdown",
            "strengths", "improvements", "recommendations",
            "job_fit_score", "matching_skills", "job_missing_skills",
            "extra_skills", "job_recommendations",
        ):
            self.assertIn(key, context)
        # Breakdown bars carry a percentage.
        for bar in context["ats_breakdown"]:
            self.assertIn("category", bar)
            self.assertIn("percent", bar)


def _minimal_payload(cache_key):
    """A small but structurally valid resume_json payload for view tests."""
    ats = {
        "ats_score": 50,
        "grade": "Moderate",
        "breakdown": {
            category: {"score": 0, "max": maximum}
            for category, maximum in CATEGORY_WEIGHTS.items()
        },
        "strengths": [],
        "improvements": [],
        "recommendations": [],
        "detected_skills": ["Python", "JavaScript"],
    }
    job = {
        "job_fit_score": 80,
        "matching_skills": ["Python"],
        "missing_skills": [],
        "extra_skills": ["JavaScript"],
        "recommendations": ["Good match."],
    }
    return {
        "_meta": {"cache_key": cache_key, "version": 1},
        "text": "Python and JavaScript",
        "is_scanned": False,
        "page_count": 1,
        "stats": {
            "word_count": 3,
            "character_count": 20,
            "has_email": False,
            "has_phone": False,
            "has_linkedin": False,
            "has_github": False,
        },
        "found_skills": ["Python", "JavaScript"],
        "missing_skills": [],
        "ats": ats,
        "job": job,
    }


class ViewIntegrationTests(TestCase):
    """End-to-end view behaviour: caching, deletion, invalid inputs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_dir = tempfile.mkdtemp(prefix="resumeai_test_media_")
        cls._media_override = override_settings(
            MEDIA_ROOT=cls._media_dir,
            STORAGES={
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                },
                # Tests render templates but never run collectstatic, so use
                # the plain storage instead of the hashed-manifest one.
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
                },
            },
        )
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass12345")
        self.client.login(username="tester", password="pass12345")

    def _create_resume(self, filename="resume.pdf", content=None, title="My Resume"):
        return Resume.objects.create(
            user=self.user,
            title=title,
            file=SimpleUploadedFile(
                filename,
                content if content is not None else make_pdf(),
                content_type="application/pdf",
            ),
        )

    def test_analyze_cache_hit_skips_pipeline(self):
        pdf = make_pdf()
        resume = self._create_resume(content=pdf)
        analysis = ResumeAnalysis.objects.create(
            resume=resume,
            job_description="Needs JS",
        )
        analysis.resume_json = _minimal_payload(build_cache_key(pdf, "Needs JS"))
        analysis.save()

        with patch(
            "resume.views.run_analysis_pipeline",
            side_effect=AssertionError("pipeline must not run on cache hit"),
        ):
            response = self.client.get(reverse("analyze_resume", args=[resume.id]))

        self.assertEqual(response.status_code, 200)
        # The cached payload must be what renders: ATS 50 / Moderate, and the
        # job-match block (job_fit_score 80 -> "Strong Match" badge).
        self.assertContains(response, "50%")
        self.assertContains(response, "Moderate")
        self.assertContains(response, "Strong Match")

    def test_analyze_corrupt_pdf_redirects_instead_of_crashing(self):
        resume = self._create_resume(content=b"not a real pdf")
        ResumeAnalysis.objects.create(resume=resume)

        response = self.client.get(reverse("analyze_resume", args=[resume.id]))

        self.assertRedirects(response, reverse("resume_history"))

    def test_analyze_missing_file_uses_cached_analysis(self):
        resume = self._create_resume()
        analysis = ResumeAnalysis.objects.create(resume=resume)
        analysis.resume_json = _minimal_payload(build_cache_key(make_pdf(), ""))
        analysis.save()

        # Remove the stored file so read_file_bytes returns None.
        if os.path.exists(resume.file.path):
            os.remove(resume.file.path)

        response = self.client.get(reverse("analyze_resume", args=[resume.id]))

        self.assertEqual(response.status_code, 200)
        # File is gone, so the only way these render is from the cached
        # resume_json payload (ATS 50 / Moderate + the "Python" match chip).
        self.assertContains(response, "50%")
        self.assertContains(response, "Python")

    def test_delete_resume_removes_file_and_analysis(self):
        resume = self._create_resume(filename="to_delete.pdf")
        ResumeAnalysis.objects.create(resume=resume)
        stored_path = resume.file.path
        self.assertTrue(os.path.exists(stored_path))

        response = self.client.get(reverse("delete_resume", args=[resume.id]))

        self.assertRedirects(response, reverse("resume_history"))
        self.assertFalse(Resume.objects.filter(id=resume.id).exists())
        self.assertFalse(ResumeAnalysis.objects.filter(resume_id=resume.id).exists())
        self.assertFalse(os.path.exists(stored_path))

    def test_dashboard_is_query_efficient(self):
        for i in range(3):
            resume = self._create_resume(filename=f"r{i}.pdf", title=f"Resume {i}")
            ResumeAnalysis.objects.create(
                resume=resume,
                ats_score=70 + i,
                job_match_score=60 + i,
            )

        with CaptureQueriesContext(connection) as captured:
            self.client.get(reverse("dashboard"))

        self.assertLessEqual(len(captured), 6)

    def test_upload_creates_resume_and_analysis(self):
        response = self.client.post(
            reverse("upload_resume"),
            {
                "title": "Integration Resume",
                "file": SimpleUploadedFile(
                    "integration.pdf",
                    make_pdf(),
                    content_type="application/pdf",
                ),
                "job_description": "Looking for Python developers.",
            },
        )

        self.assertRedirects(
            response,
            reverse("analyze_resume", args=[Resume.objects.get().id]),
        )
        resume = Resume.objects.get(user=self.user, title="Integration Resume")
        self.assertTrue(hasattr(resume, "analysis"))
        self.assertEqual(
            resume.analysis.job_description,
            "Looking for Python developers.",
        )

    def test_upload_invalid_form_rerenders(self):
        # No title/file supplied -> form is invalid and no rows are created.
        response = self.client.post(reverse("upload_resume"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload Resume")
        self.assertEqual(Resume.objects.count(), 0)

    def test_history_lists_resumes_for_current_user_only(self):
        mine = self._create_resume(title="Visible Resume")
        ResumeAnalysis.objects.create(resume=mine, ats_score=88)
        other = User.objects.create_user(username="other", password="pass12345")
        their_resume = Resume.objects.create(
            user=other,
            title="Invisible Resume",
            file=SimpleUploadedFile(
                "other.pdf",
                make_pdf(),
                content_type="application/pdf",
            ),
        )

        response = self.client.get(reverse("resume_history"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible Resume")
        self.assertContains(response, "88")
        self.assertNotContains(response, "Invisible Resume")
        self.assertTrue(their_resume.pk)  # sanity: fixture row exists
