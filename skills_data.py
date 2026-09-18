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
    "public_health_mel": [
        "monitoring evaluation and learning", "monitoring and evaluation",
        "routine immunization", "health management information system",
        "routine health information system", "dhis2", "dhis2 submission",
        "routine immunization sms platform", "mobile immunization team",
        "data quality assurance", "data quality assessment", "data collection",
        "data collectors", "mobile data collection", "database management",
        "project database", "mel framework", "mel plan", "workplan",
        "project deliverables", "indicator tracking table", "performance monitoring",
        "programme reporting", "data review meeting", "microplanning",
        "outreach planning", "supportive supervision", "capacity building",
        "quantitative analysis", "qualitative analysis", "analysis plans",
        "community health workers", "volunteers", "lessons learned",
        "kobotoolbox", "odk", "xlsform", "commcare", "surveycto",
        "power bi", "dashboard", "gis", "spatial analysis",
    ],
}

# Flattened list of every skill/keyword the scorer will search for.
ALL_SKILLS = sorted({s.lower() for group in SKILL_BANK.values() for s in group})

# Canonical skill -> accepted equivalent wording.  The scorer reports the
# canonical label while recording whether the resume used the exact JD wording
# or a defensible alias.  Narrow aliases are deliberate: they improve recall
# without pretending that vaguely related experience is the same requirement.
SKILL_ALIASES = {
    "monitoring evaluation and learning": [
        "monitoring, evaluation and learning", "monitoring, evaluation, and learning",
        "mel", "monitoring evaluation accountability and learning",
    ],
    "monitoring and evaluation": ["m&e", "monitoring & evaluation"],
    "routine immunization": ["routine immunisation"],
    "health management information system": ["health management information systems", "hmis"],
    "routine health information system": ["routine health information systems", "rhis"],
    "dhis2 submission": ["submit data into dhis2", "submission into dhis2", "data submission to dhis2"],
    "routine immunization sms platform": [
        "routine immunisation sms platform", "ri sms platform", "ri-sms platform",
    ],
    "mobile immunization team": ["mobile immunisation team", "mobile immunization teams"],
    "data quality assurance": ["quality assurance", "data qa", "qc/qa", "data quality control"],
    "data quality assessment": ["data quality assessments", "dqa", "dqas"],
    "data collectors": ["data collector", "enumerators", "field data collectors"],
    "mobile data collection": ["phone-based data collection", "digital data collection"],
    "database management": ["manage databases", "managing databases"],
    "project database": ["project databases", "structured database", "structured databases"],
    "mel framework": ["mel frameworks", "mel plan", "mel plans"],
    "mel plan": ["mel plans", "m&e plan", "monitoring and evaluation plan"],
    "workplan": ["workplans", "work plan", "work plans"],
    "project deliverables": ["project deliverable", "reporting deliverables"],
    "indicator tracking table": ["indicator tracking tables", "indicator tracker", "indicator trackers"],
    "data review meeting": [
        "data-review meeting", "data review meetings", "data-review meetings",
        "data review discussion", "data review discussions", "data-review discussion",
        "data-review discussions", "review sessions",
    ],
    "analysis plans": [
        "analysis plan", "quantitative analysis plan", "qualitative analysis plan",
        "quantitative and qualitative analysis plans", "data analysis plan",
    ],
    "community health workers": ["community health worker", "chws", "chw"],
    "quantitative analysis": [
        "quantitative data analysis", "analyzed quantitative monitoring data",
        "analysed quantitative monitoring data",
    ],
    "qualitative analysis": [
        "qualitative feedback analysis", "qualitative community feedback analysis",
        "analyzed qualitative community feedback", "analysed qualitative community feedback",
        "qualitative community feedback",
    ],
    "lessons learned": ["lessons learnt", "learning documentation"],
    "kobotoolbox": ["kobo toolbox", "kobo"],
    "odk": ["open data kit"],
    "power bi": ["powerbi"],
    "dashboard": ["dashboards"],
}

# Higher weights are reserved for requirements that commonly function as
# screening gates or that materially distinguish the role.  These weights are
# transparent and can be defended or tuned without changing the algorithm.
SKILL_WEIGHTS = {
    "monitoring evaluation and learning": 1.5,
    "routine immunization": 1.5,
    "dhis2": 1.5,
    "dhis2 submission": 1.8,
    "routine immunization sms platform": 2.0,
    "mobile immunization team": 1.8,
    "data collectors": 1.5,
    "mel framework": 1.5,
    "analysis plans": 1.5,
}

# Requirement -> (supporting canonical skills, fractional credit).  These rules
# recognise transferable evidence while keeping the target requirement in the
# missing/gap list.  They must never convert a platform- or context-specific gap
# into a direct match.
TRANSFERABLE_EVIDENCE = {
    "mobile immunization team": ({"routine immunization", "data collectors"}, 0.50),
    "analysis plans": ({"quantitative analysis", "qualitative analysis"}, 0.50),
    "dhis2 submission": ({"dhis2"}, 0.35),
    "community health workers": ({"data collectors"}, 0.35),
    "volunteers": ({"data collectors"}, 0.25),
    "lessons learned": ({"monitoring evaluation and learning"}, 0.25),
    "routine immunization sms platform": ({"routine immunization", "mobile data collection"}, 0.20),
}

# Words that indicate a quantified, achievement-oriented bullet point.
IMPACT_SIGNAL_WORDS = [
    "increased", "decreased", "reduced", "improved", "achieved", "grew",
    "generated", "saved", "led", "built", "launched", "delivered",
    "optimized", "automated", "designed", "implemented", "managed",
    "developed", "trained", "coached", "supported", "provided", "conducted",
    "analyzed", "analysed", "facilitated", "maintained", "validated",
    "reconciled", "coordinated", "supervised",
    "increase", "decrease", "reduce", "improve", "achieve", "grow",
    "generate", "save", "lead", "build", "launch", "deliver", "optimize",
    "automate", "design", "implement", "manage", "develop", "train", "coach",
    "support", "provide", "conduct", "analyze", "analyse", "facilitate",
    "maintain", "validate", "reconcile", "coordinate", "supervise",
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
