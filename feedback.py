"""
feedback.py

Converts the raw ScoreResult + heuristic checks into plain-language,
actionable feedback a candidate can act on before re-submitting their resume.
"""

from scorer import ScoreResult, count_impact_bullets, has_contact_info


def generate_feedback(resume_text: str, result: ScoreResult) -> list:
    tips = []

    if result.jd_skill_count == 0:
        tips.append(
            "The current keyword bank did not extract any scorable requirements from this job description. "
            "Do not interpret the overall score as a full ATS assessment; review the JD manually or extend the bank."
        )
    elif result.missing_skills:
        shown = ", ".join(result.missing_skills[:8])
        extra = f" (+{len(result.missing_skills) - 8} more)" if len(result.missing_skills) > 8 else ""
        tips.append(
            f"Requirements detected in the job description but not in the resume: {shown}{extra}. "
            "Add them only when your verified experience supports the claim; otherwise record them as genuine gaps."
        )
    else:
        tips.append(
            "No requirement keywords are missing from the current bank. This is not proof that every qualification "
            "is met; confirm eligibility, depth of experience and application instructions manually."
        )

    if result.transferable_matches:
        shown = ", ".join(result.transferable_matches[:8])
        extra = f" (+{len(result.transferable_matches) - 8} more)" if len(result.transferable_matches) > 8 else ""
        tips.append(
            f"Transferable evidence was found for: {shown}{extra}. These receive partial credit but remain direct-experience gaps."
        )

    if result.skills_only_matches:
        shown = ", ".join(result.skills_only_matches[:8])
        extra = f" (+{len(result.skills_only_matches) - 8} more)" if len(result.skills_only_matches) > 8 else ""
        tips.append(
            f"These matches were found outside the professional-experience section: {shown}{extra}. "
            "Where truthful, demonstrate them in a role bullet rather than relying on a profile or skills list."
        )

    if result.alias_matches:
        shown = ", ".join(result.alias_matches[:8])
        extra = f" (+{len(result.alias_matches) - 8} more)" if len(result.alias_matches) > 8 else ""
        tips.append(
            f"Equivalent wording was accepted for: {shown}{extra}. Review the JD's exact terminology before submission."
        )

    if result.skill_coverage_pct < 50:
        tips.append(
            "Your skill-keyword coverage is below 50%. Consider tailoring this resume specifically to this "
            "role rather than sending a generic version — pull 2–3 exact phrases from the job description "
            "into your skills or experience section."
        )

    impact_count = count_impact_bullets(resume_text)
    if impact_count < 3:
        tips.append(
            f"Only {impact_count} experience bullet(s) combine an action with a number. Add verified scope or results "
            "where they materially strengthen the evidence; do not invent metrics merely to raise the score."
        )

    if result.removed_jd_noise:
        tips.append(
            f"Removed {len(result.removed_jd_noise)} job-board control line(s) before scoring so navigation text did not distort the result."
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
        "evidence_before": pre.evidence_coverage_pct,
        "evidence_after": post.evidence_coverage_pct,
    }
