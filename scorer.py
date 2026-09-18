"""
Transparent, offline resume-to-job matching engine.

The score is deliberately split into three inspectable components:
- text similarity (word/character TF-IDF, not labelled as AI semantics);
- weighted requirement-keyword coverage;
- evidence placement (whether matched requirements appear in experience).

The engine is a decision-support aid. It cannot reproduce an employer's ATS
configuration or prove that a candidate meets a requirement.
"""

import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from parser import clean_job_description
from skills_data import (
    ALL_SKILLS,
    IMPACT_SIGNAL_WORDS,
    SKILL_ALIASES,
    SKILL_WEIGHTS,
    SYNONYM_GROUPS,
    TRANSFERABLE_EVIDENCE,
)


_SYNONYM_LOOKUP = []
for group in SYNONYM_GROUPS:
    canonical = group[0]
    for term in group:
        _SYNONYM_LOOKUP.append((term.lower(), canonical))
_SYNONYM_LOOKUP.sort(key=lambda pair: len(pair[0]), reverse=True)


def _normalise_phrase_text(text: str) -> str:
    """Normalise punctuation while retaining technical tokens such as C++."""
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[-/_,:;()\[\]{}|]", " ", text)
    text = re.sub(r"[^a-z0-9+.#\s]", " ", text)
    return " " + re.sub(r"\s+", " ", text).strip() + " "


def _term_present(text: str, term: str, *, text_is_normalised: bool = False) -> bool:
    normal_text = text if text_is_normalised else _normalise_phrase_text(text)
    normal_term = _normalise_phrase_text(term).strip()
    if not normal_term:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(normal_term) + r"(?![a-z0-9])"
    return bool(re.search(pattern, normal_text))


def _normalise_for_similarity(text: str) -> str:
    """Map narrow synonym groups and normalise text for TF-IDF."""
    text_lower = _normalise_phrase_text(text).strip()
    for term, canonical in _SYNONYM_LOOKUP:
        term_norm = _normalise_phrase_text(term).strip()
        pattern = r"(?<![a-z0-9])" + re.escape(term_norm) + r"(?![a-z0-9])"
        text_lower = re.sub(pattern, canonical.replace(" ", "_"), text_lower)
    return text_lower


@dataclass
class ScoreResult:
    overall_score: float
    skill_coverage_pct: float
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)
    combined_score: float = 0.0
    evidence_coverage_pct: float = 0.0
    exact_matches: list = field(default_factory=list)
    alias_matches: list = field(default_factory=list)
    experience_supported_skills: list = field(default_factory=list)
    skills_only_matches: list = field(default_factory=list)
    transferable_matches: list = field(default_factory=list)
    jd_skill_count: int = 0
    removed_jd_noise: list = field(default_factory=list)


def _skill_matches(text: str) -> dict:
    """Return canonical skill -> metadata for exact and alias matches."""
    matches = {}
    normal_text = _normalise_phrase_text(text)
    for skill in ALL_SKILLS:
        if _term_present(normal_text, skill, text_is_normalised=True):
            matches[skill] = {"match_type": "exact", "matched_term": skill}
            continue
        for alias in SKILL_ALIASES.get(skill, []):
            if _term_present(normal_text, alias, text_is_normalised=True):
                matches[skill] = {"match_type": "alias", "matched_term": alias}
                break
    return matches


def _find_skills(text: str) -> set:
    """Backward-compatible helper used by earlier notebooks/tests."""
    return set(_skill_matches(text))


def _cosine_tfidf(resume: str, jd: str, **vectorizer_kwargs) -> float:
    vectorizer = TfidfVectorizer(**vectorizer_kwargs)
    try:
        matrix = vectorizer.fit_transform([resume, jd])
    except ValueError:
        return 0.0
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])


def _tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """
    Explainable lexical similarity using both word and character features.

    Character n-grams add limited spelling/word-form resilience; this remains
    lexical similarity and is intentionally not called semantic AI.
    """
    resume_norm = _normalise_for_similarity(resume_text)
    jd_norm = _normalise_for_similarity(jd_text)
    word_score = _cosine_tfidf(
        resume_norm,
        jd_norm,
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    char_score = _cosine_tfidf(
        resume_norm,
        jd_norm,
        analyzer="char_wb",
        ngram_range=(3, 5),
        sublinear_tf=True,
        min_df=1,
    )
    return round(((word_score * 0.7) + (char_score * 0.3)) * 100, 1)


_EXPERIENCE_START = re.compile(
    r"^(professional|work|employment|relevant) experience$", re.IGNORECASE
)
_EXPERIENCE_END = re.compile(
    r"^(education|academic background|qualifications|technical skills|skills|certifications|references|mobility)$",
    re.IGNORECASE,
)


def _extract_experience_text(resume_text: str) -> str:
    lines = [line.strip() for line in resume_text.splitlines()]
    start = None
    for index, line in enumerate(lines):
        if _EXPERIENCE_START.match(line):
            start = index + 1
            break
    if start is None:
        return ""

    end = len(lines)
    for index in range(start, len(lines)):
        if _EXPERIENCE_END.match(lines[index]):
            end = index
            break
    return "\n".join(lines[start:end])


def score_resume(resume_text: str, jd_text: str) -> ScoreResult:
    if not resume_text.strip() or not jd_text.strip():
        raise ValueError("Both the resume and the job description must contain text.")

    cleaned_jd, removed_noise = clean_job_description(jd_text)
    text_similarity = _tfidf_similarity(resume_text, cleaned_jd)

    jd_matches = _skill_matches(cleaned_jd)
    resume_matches = _skill_matches(resume_text)
    jd_skills = set(jd_matches)
    resume_skills = set(resume_matches)

    matched = jd_skills & resume_skills
    missing = jd_skills - resume_skills
    transferable = set()
    for requirement in missing:
        rule = TRANSFERABLE_EVIDENCE.get(requirement)
        if rule and rule[0].issubset(resume_skills):
            transferable.add(requirement)

    if jd_skills:
        coverage_denominator = sum(SKILL_WEIGHTS.get(skill, 1.0) for skill in jd_skills)
        coverage_points = sum(SKILL_WEIGHTS.get(skill, 1.0) for skill in matched)
        coverage_points += sum(
            SKILL_WEIGHTS.get(skill, 1.0) * TRANSFERABLE_EVIDENCE[skill][1]
            for skill in transferable
        )
        coverage = round((coverage_points / coverage_denominator) * 100, 1)
    else:
        coverage = 0.0

    experience_text = _extract_experience_text(resume_text)
    experience_matches = set(_skill_matches(experience_text)) if experience_text else set()
    experience_supported = matched & experience_matches
    skills_only = matched - experience_supported

    if jd_skills:
        denominator = sum(SKILL_WEIGHTS.get(skill, 1.0) for skill in jd_skills)
        evidence_points = sum(SKILL_WEIGHTS.get(skill, 1.0) for skill in experience_supported)
        evidence_points += 0.45 * sum(SKILL_WEIGHTS.get(skill, 1.0) for skill in skills_only)
        for requirement in transferable:
            support, credit = TRANSFERABLE_EVIDENCE[requirement]
            support_factor = 1.0 if support.issubset(experience_matches) else 0.45
            evidence_points += SKILL_WEIGHTS.get(requirement, 1.0) * credit * support_factor
        evidence_coverage = round((evidence_points / denominator) * 100, 1)
        combined = round(
            (text_similarity * 0.15) + (coverage * 0.45) + (evidence_coverage * 0.40),
            1,
        )
    else:
        evidence_coverage = 0.0
        combined = round(text_similarity * 0.6, 1)

    exact = sorted(skill for skill in matched if resume_matches[skill]["match_type"] == "exact")
    alias = sorted(skill for skill in matched if resume_matches[skill]["match_type"] == "alias")

    return ScoreResult(
        overall_score=text_similarity,
        skill_coverage_pct=coverage,
        matched_skills=sorted(matched),
        missing_skills=sorted(missing),
        combined_score=combined,
        evidence_coverage_pct=evidence_coverage,
        exact_matches=exact,
        alias_matches=alias,
        experience_supported_skills=sorted(experience_supported),
        skills_only_matches=sorted(skills_only),
        transferable_matches=sorted(transferable),
        jd_skill_count=len(jd_skills),
        removed_jd_noise=removed_noise,
    )


_BULLET_START = re.compile(r"^\s*(?:[-*•▪◦‣]|\d+[.)])\s+")


def _logical_bullets(resume_text: str) -> list[str]:
    """Join wrapped PDF/DOCX bullet lines before measuring impact."""
    bullets = []
    current = ""
    for raw_line in resume_text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                bullets.append(current)
                current = ""
            continue
        if _BULLET_START.match(line):
            if current:
                bullets.append(current)
            current = _BULLET_START.sub("", line)
        elif current and not (line.isupper() and len(line.split()) <= 8):
            current += " " + line
        elif current:
            bullets.append(current)
            current = ""
    if current:
        bullets.append(current)

    if bullets:
        return bullets
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", resume_text) if part.strip()]


def count_impact_bullets(resume_text: str) -> int:
    """Count logical bullets containing both a number and an action signal."""
    count = 0
    for bullet in _logical_bullets(resume_text):
        low = bullet.lower()
        has_number = bool(re.search(r"\b\d[\d,]*(?:\.\d+)?\b|\b\d+(?:st|nd|rd|th)\b", bullet))
        has_signal_word = any(re.search(rf"\b{re.escape(word)}\b", low) for word in IMPACT_SIGNAL_WORDS)
        if has_number and has_signal_word:
            count += 1
    return count


def has_contact_info(resume_text: str) -> dict:
    email_found = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text))
    phone_found = bool(re.search(r"(\+?\d[\d\-\s()]{7,}\d)", resume_text))
    return {"email": email_found, "phone": phone_found}
