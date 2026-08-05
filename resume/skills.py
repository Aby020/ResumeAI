"""
Expanded skill taxonomy + category relevance weights.

This module is the single source of truth for canonical skill names and their
categories. Surface spellings (JS, ML, React.js, ...) live in nlp/aliases.py.
"""
from collections import OrderedDict

from .nlp.aliases import EXTRA_ALIASES

# Category name -> canonical skill names
SKILL_CATEGORIES = OrderedDict([
    ("Programming Languages", [
        "Python", "JavaScript", "TypeScript", "Java", "C", "C++", "C#",
        "Go", "Rust", "Kotlin", "Swift", "Ruby", "PHP", "Scala", "Dart",
        "R", "MATLAB", "Objective-C", "Bash", "PowerShell", "Perl",
        "Haskell", "Lua", "Groovy", "Solidity",
    ]),
    ("Frontend & Web", [
        "HTML", "CSS", "Sass", "Tailwind CSS", "Bootstrap", "React",
        "Next.js", "Vue.js", "Angular", "jQuery", "Redux", "Webpack",
        "Vite", "GraphQL", "Three.js",
    ]),
    ("Mobile & Cross-Platform", [
        "React Native", "Flutter", "Xamarin",
    ]),
    ("Backend & Frameworks", [
        "Django", "Flask", "FastAPI", "Spring", "Spring Boot", "Node.js",
        "Express", "NestJS", "Laravel", "ASP.NET", "Ruby on Rails",
        "Hibernate", "Celery", "RabbitMQ", "Kafka", "gRPC", "REST APIs",
    ]),
    ("Databases & Data Stores", [
        "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Oracle", "SQL Server", "Cassandra", "MariaDB", "Firebase",
        "Snowflake", "BigQuery", "Redshift", "Neo4j", "SQL",
    ]),
    ("Cloud, DevOps & Infrastructure", [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
        "Jenkins", "GitHub Actions", "GitLab CI", "Nginx", "Vercel", "Netlify",
        "Helm", "Prometheus", "Grafana", "Linux", "Unix", "CloudFormation",
        "CI/CD", "Microservices",
    ]),
    ("AI, ML & Data", [
        "TensorFlow", "PyTorch", "Keras", "scikit-learn", "NumPy", "Pandas",
        "Hugging Face", "OpenAI", "LangChain", "Machine Learning",
        "Artificial Intelligence", "Deep Learning",
        "Natural Language Processing", "Computer Vision",
        "OpenCV", "Data Science", "Data Analysis", "Data Engineering",
        "ETL", "Apache Spark", "Apache Airflow", "dbt", "Large Language Models",
        "RAG", "Recommender Systems", "MLOps", "NLTK", "Time Series",
        "A/B Testing",
    ]),
    ("Tools & Platforms", [
        "Git", "GitHub", "GitLab", "Bitbucket", "Postman", "Jira",
        "Confluence", "Figma", "VS Code", "IntelliJ", "Android Studio",
        "Slack", "Zoom", "Excel", "PowerPoint", "Tableau", "Power BI",
        "Looker", "Jupyter", "Selenium", "Cypress", "Jest", "Mocha",
        "PyTest", "JUnit",
    ]),
    ("Soft Skills", [
        "Communication", "Teamwork", "Leadership", "Problem Solving",
        "Critical Thinking", "Time Management", "Agile", "Scrum", "Kanban",
        "Adaptability", "Collaboration", "Mentoring", "Presentation",
        "Conflict Resolution", "Project Management", "Decision Making",
    ]),
])

CATEGORY_WEIGHTS = {
    "Programming Languages": 1.0,
    "Frontend & Web": 1.0,
    "Mobile & Cross-Platform": 1.0,
    "Backend & Frameworks": 1.0,
    "Databases & Data Stores": 1.0,
    "Cloud, DevOps & Infrastructure": 1.0,
    "AI, ML & Data": 1.0,
    "Tools & Platforms": 0.8,
    "Soft Skills": 0.4,
}

# canonical skill -> category (derived, insertion-ordered, de-duplicated)
SKILL_CATEGORY_OF = {
    name: category
    for category, names in SKILL_CATEGORIES.items()
    for name in names
}

# Flat canonical list (kept for backward compatibility with older importers).
SKILLS = tuple(SKILL_CATEGORY_OF.keys())

# Curated high-value skills used to suggest commonly-missing keywords.
COMMON_SKILLS = (
    "Python", "JavaScript", "TypeScript", "Java", "SQL", "HTML", "CSS",
    "React", "Node.js", "Django", "Flask", "PostgreSQL", "MySQL", "MongoDB",
    "Redis", "AWS", "Docker", "Kubernetes", "Git", "GitHub",
    "Machine Learning", "TensorFlow", "PyTorch", "NumPy", "Pandas",
    "REST APIs", "GraphQL", "CI/CD", "Terraform", "Linux", "Agile",
    "Communication", "Teamwork", "Problem Solving",
)

# Validate: every alias must reference a real canonical skill (catches typos).
_unknown = set(EXTRA_ALIASES) - set(SKILL_CATEGORY_OF)
if _unknown:
    raise ValueError(
        f"Aliases reference unknown skills (missing from taxonomy): {sorted(_unknown)}"
    )
