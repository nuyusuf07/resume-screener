"""
scorer.py

The core matching engine. No external model downloads are required:
- Overall match score uses TF-IDF + cosine similarity (scikit-learn).
- Skill coverage uses simple, robust keyword matching against skills_data.py.

This keeps the system fully offline-runnable, which matters for a student
project defended on a lab machine that may not always have internet access.
"""

import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import PorterStemmer

from skills_data import ALL_SKILLS, IMPACT_SIGNAL_WORDS, SYNONYM_GROUPS

_stemmer = PorterStemmer()

# Build a lookup: every term in a synonym group -> the group's first term
# (the "canonical" form), longest terms first so multi-word phrases match
# before their shorter substrings do.
_SYNONYM_LOOKUP = []
for group in SYNONYM_GROUPS:
    canonical = group[0]
    for term in group:
        _SYNONYM_LOOKUP.append((term.lower(), canonical))
_SYNONYM_LOOKUP.sort(key=lambda pair: len(pair[0]), reverse=True)


def _normalize_for_similarity(text: str) -> str:
    """
    Prepares text for TF-IDF comparison by:
    1. Replacing known synonym/related terms with one shared canonical word,
       so e.g. "immunization" and "vaccine" both become the same token.
    2. Stemming every remaining word (Porter stemmer), so word-form
       differences like "modelling" vs "models" vs "modelled" collapse to
       the same root.
    Both steps run fully offline — no model downloads required.
    """
    text_lower = text.lower()
    for term, canonical in _SYNONYM_LOOKUP:
        pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
        text_lower = re.sub(pattern, canonical.replace(" ", "_"), text_lower)

    words = re.findall(r"[a-z0-9_]+", text_lower)
    stemmed = [_stemmer.stem(w) for w in words]
    return " ".join(stemmed)


@dataclass
class ScoreResult:
    overall_score: float          # 0-100, similarity between resume and JD
    skill_coverage_pct: float     # 0-100, % of JD skills found in resume
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)
    combined_score: float = 0.0   # blended final score shown to the user


def _find_skills(text: str) -> set:
    text_lower = " " + re.sub(r"[^a-z0-9+.# ]", " ", text.lower()) + " "
    found = set()
    for skill in ALL_SKILLS:
        # word-boundary-ish match so "r" doesn't match inside "reduced"
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            found.add(skill)
    return found


def _tfidf_similarity(resume_text: str, jd_text: str) -> float:
    resume_norm = _normalize_for_similarity(resume_text)
    jd_norm = _normalize_for_similarity(jd_text)

    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_norm, jd_norm])
    except ValueError:
        # happens if one of the documents is empty after stop-word removal
        return 0.0
    sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return round(sim * 100, 1)


def score_resume(resume_text: str, jd_text: str) -> ScoreResult:
    if not resume_text.strip() or not jd_text.strip():
        raise ValueError("Both the resume and the job description must contain text.")

    overall = _tfidf_similarity(resume_text, jd_text)

    jd_skills = _find_skills(jd_text)
    resume_skills = _find_skills(resume_text)

    matched = sorted(jd_skills & resume_skills)
    missing = sorted(jd_skills - resume_skills)

    coverage = round((len(matched) / len(jd_skills)) * 100, 1) if jd_skills else 100.0

    # Blend: 60% semantic similarity, 40% skill coverage.
    # Skill coverage is weighted in because recruiters and ATS tools often
    # filter on hard keyword hits even when overall phrasing differs.
    combined = round((overall * 0.6) + (coverage * 0.4), 1)

    return ScoreResult(
        overall_score=overall,
        skill_coverage_pct=coverage,
        matched_skills=matched,
        missing_skills=missing,
        combined_score=combined,
    )


def count_impact_bullets(resume_text: str) -> int:
    """Rough count of lines that read like a quantified achievement."""
    lines = resume_text.split("\n")
    count = 0
    for line in lines:
        low = line.lower()
        has_number = bool(re.search(r"\d", line))
        has_signal_word = any(w in low for w in IMPACT_SIGNAL_WORDS)
        if has_number and has_signal_word:
            count += 1
    return count


def has_contact_info(resume_text: str) -> dict:
    email_found = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text))
    phone_found = bool(re.search(r"(\+?\d[\d\-\s()]{7,}\d)", resume_text))
    return {"email": email_found, "phone": phone_found}
