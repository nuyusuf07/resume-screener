"""
skills_data.py

A curated bank of skills/keywords the scorer looks for. This is intentionally
a plain Python dictionary (not a downloaded model) so the whole system runs
offline with no external API keys or model downloads required.

Feel free to extend SKILL_BANK with more terms relevant to the roles you're
targeting (e.g. add "QGIS", "ArcGIS", "remote sensing" for a GIS-heavy job,
or "Laravel", "Figma" for a web/design role).
"""

SKILL_BANK = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "php", "sql", "r", "go", "golang", "kotlin", "swift", "ruby",
        "matlab", "html", "css", "bash", "shell scripting", "dart",
    ],
    "data_ml": [
        "machine learning", "deep learning", "natural language processing",
        "nlp", "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow",
        "pytorch", "keras", "data analysis", "data visualization",
        "power bi", "tableau", "statistics", "regression", "classification",
        "clustering", "computer vision", "opencv", "big data", "etl",
    ],
    "web_dev": [
        "react", "angular", "vue", "node.js", "nodejs", "express",
        "django", "flask", "fastapi", "rest api", "graphql", "bootstrap",
        "tailwind", "next.js", "redux", "webpack",
    ],
    "databases": [
        "mysql", "postgresql", "mongodb", "sqlite", "oracle", "firebase",
        "redis", "nosql", "database design", "data warehousing",
    ],
    "devops_tools": [
        "git", "github", "gitlab", "docker", "kubernetes", "aws", "azure",
        "google cloud", "gcp", "ci/cd", "jenkins", "linux", "agile",
        "scrum", "jira",
    ],
    "gis_geospatial": [
        "gis", "arcgis", "qgis", "remote sensing", "spatial analysis",
        "geospatial", "kobo toolbox", "kml", "shapefile", "geopandas",
        "postgis", "cartography",
    ],
    "soft_skills": [
        "communication", "leadership", "teamwork", "problem solving",
        "project management", "time management", "collaboration",
        "critical thinking", "presentation", "stakeholder management",
    ],
    "general_cs": [
        "data structures", "algorithms", "object-oriented programming",
        "oop", "software engineering", "system design", "testing",
        "debugging", "api integration", "cybersecurity", "networking",
        "cloud computing", "mobile development", "android", "ios",
    ],
}

# Flattened list of every skill/keyword the scorer will search for.
ALL_SKILLS = sorted({s.lower() for group in SKILL_BANK.values() for s in group})

# Words that indicate a quantified, achievement-oriented bullet point.
IMPACT_SIGNAL_WORDS = [
    "increased", "decreased", "reduced", "improved", "achieved", "grew",
    "generated", "saved", "led", "built", "launched", "delivered",
    "optimized", "automated", "designed", "implemented", "managed",
]

# Domain-specific synonym groups. Each group maps a set of related terms
# (that TF-IDF would otherwise treat as completely unrelated words) to one
# shared canonical token, so a resume that says "vaccination campaign
# monitoring" gets credit against a job description that says "immunization
# coverage" — without needing an internet-dependent embedding model.
#
# This is intentionally curated by hand and kept small: every mapping here
# should be defensible in a viva ("why does the system think X relates to
# Y?") rather than a black-box association.
SYNONYM_GROUPS = [
    ["vaccine", "vaccination", "vaccinated", "immunization", "immunisation", "immunity", "immune"],
    ["serological", "serology", "seroprevalence", "sero-surveillance", "serosurvey"],
    ["spatiotemporal", "space-time", "spatio-temporal"],
    ["geospatial", "spatial"],
    ["inequity", "inequality", "disparity", "disadvantage"],
    ["coverage", "uptake"],
    ["modelling", "modeling", "model"],
    ["supplementary immunization activity", "sia", "outreach campaign", "catch-up campaign"],
]

