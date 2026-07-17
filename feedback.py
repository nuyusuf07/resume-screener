"""
feedback.py

Converts the raw ScoreResult + heuristic checks into plain-language,
actionable feedback a candidate can act on before re-submitting their resume.
"""

from scorer import ScoreResult, count_impact_bullets, has_contact_info


def generate_feedback(resume_text: str, result: ScoreResult) -> list:
    tips = []

    if result.missing_skills:
        shown = ", ".join(result.missing_skills[:8])
        extra = f" (+{len(result.missing_skills) - 8} more)" if len(result.missing_skills) > 8 else ""
        tips.append(
            f"Missing keywords the job description mentions but your resume doesn't: {shown}{extra}. "
            "If you genuinely have these skills, add them explicitly — ATS tools match on exact wording, "
            "not on your job title alone."
        )
    else:
        tips.append("Good news — your resume already contains every skill keyword found in the job description.")

    if result.skill_coverage_pct < 50:
        tips.append(
            "Your skill-keyword coverage is below 50%. Consider tailoring this resume specifically to this "
            "role rather than sending a generic version — pull 2–3 exact phrases from the job description "
            "into your skills or experience section."
        )

    impact_count = count_impact_bullets(resume_text)
    if impact_count < 2:
        tips.append(
            "Only a few of your bullet points show measurable impact (a number + an action verb, e.g. "
            "'reduced processing time by 30%'). Recruiters and screening software both weigh quantified "
            "achievements heavily — try rewriting at least 3–4 bullets this way."
        )

    contact = has_contact_info(resume_text)
    if not contact["email"]:
        tips.append("No email address was detected — make sure a professional email is clearly visible near the top.")
    if not contact["phone"]:
        tips.append("No phone number was detected — add one so recruiters can reach you directly.")

    word_count = len(resume_text.split())
    if word_count < 150:
        tips.append(
            f"Your resume is quite short ({word_count} words). It may be missing enough detail on your "
            "projects or experience for a screening algorithm to confidently match you to this role."
        )
    elif word_count > 900:
        tips.append(
            f"Your resume is fairly long ({word_count} words). Consider trimming to the most relevant "
            "experience for this specific role — most recruiters spend under a minute on a first pass."
        )

    if not tips:
        tips.append("Your resume looks well-aligned with this job description. Nice work.")

    return tips


def compare_scores(pre: ScoreResult, post: ScoreResult) -> dict:
    return {
        "score_before": pre.combined_score,
        "score_after": post.combined_score,
        "delta": round(post.combined_score - pre.combined_score, 1),
        "skills_gained": sorted(set(post.matched_skills) - set(pre.matched_skills)),
        "still_missing": sorted(post.missing_skills),
    }
