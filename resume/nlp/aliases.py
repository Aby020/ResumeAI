"""
Skill alias graph — extra surface spellings that resolve to a canonical name.

The canonical name itself (lowercased) is always a valid variant, so this map
only lists spellings that are NOT derived from the name by simple lowercasing:
abbreviations, common tech shorthand, and punctuation variants.

Examples:
    JS            -> JavaScript
    Python3 / py3 -> Python
    React.js      -> React
    NodeJS        -> Node.js
    ML            -> Machine Learning
    AI            -> Artificial Intelligence
    K8s           -> Kubernetes

Keys MUST exist in resume/skills.py's taxonomy (validated at import time).
"""

EXTRA_ALIASES = {
    # Programming languages
    "Python": ["python3", "py3", "python 3"],
    "JavaScript": ["js", "es6", "ecmascript", "java script"],
    "TypeScript": ["ts"],
    "C": ["c/c++", "ansi c", "c programming", "c language", "c (programming)"],
    "C++": ["cpp", "cplusplus"],
    "C#": ["csharp", "c sharp"],
    "Go": ["golang", "go lang", "go (programming)"],
    "R": ["r programming", "r language", "rstudio"],
    "Bash": ["shell script", "shell scripting"],
    "Objective-C": ["objective c", "obj-c", "objc"],

    # Frontend & web
    "React": ["react.js", "reactjs", "react js"],
    "Next.js": ["nextjs", "next js"],
    "Vue.js": ["vuejs", "vue js"],
    "Tailwind CSS": ["tailwind"],
    "Sass": ["scss"],
    "GraphQL": ["gql"],

    # Mobile & cross-platform
    "React Native": ["reactnative", "react native (rn)"],

    # Backend & frameworks
    "Node.js": ["nodejs", "node js", "node"],
    "Express": ["expressjs", "express js"],
    "NestJS": ["nestjs", "nest js"],
    "Spring Boot": ["springboot"],
    "ASP.NET": ["asp.net", "asp net", ".net", "dotnet"],
    "Ruby on Rails": ["rails", "ror"],
    "REST APIs": ["rest api", "rest apis", "restful", "restful api", "restful apis"],
    "Kafka": ["apache kafka"],

    # Databases & data stores
    "PostgreSQL": ["postgres", "psql"],
    "SQLite": ["sqlite3"],
    "MongoDB": ["mongo"],
    "Elasticsearch": ["elastic search"],
    "SQL Server": ["mssql"],
    "Firebase": ["firestore"],

    # Cloud, DevOps & infrastructure
    "AWS": ["amazon web services"],
    "Kubernetes": ["k8s"],
    "GitHub Actions": ["github action", "gh actions", "gh action"],
    "CI/CD": ["cicd"],
    "OpenAI": ["open ai"],

    # AI, ML & data
    "Machine Learning": ["ml"],
    "Artificial Intelligence": ["ai"],
    "Natural Language Processing": ["nlp"],
    "Large Language Models": ["llm", "llms"],
    "TensorFlow": ["tensor flow"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "OpenCV": ["cv2"],
    "Apache Spark": ["spark"],
    "Apache Airflow": ["airflow"],
    "Hugging Face": ["huggingface"],
    "Computer Vision": ["computer vision"],

    # Tools & platforms
    "VS Code": ["visual studio code", "vscode"],
    "Power BI": ["powerbi"],
    "Excel": ["ms excel", "microsoft excel"],
    "Jupyter": ["jupyter notebook"],
    "PyTest": ["pytest"],
}
