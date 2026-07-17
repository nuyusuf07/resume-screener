"""
app.py

Pre-Post Resume Screening and Feedback System
Run with:  streamlit run app.py
"""

import datetime
import os

import pandas as pd
import streamlit as st

from parser import extract_text
from scorer import score_resume
from feedback import generate_feedback, compare_scores

st.set_page_config(page_title="Resume Screening System", page_icon="📄", layout="wide")

HISTORY_FILE = "scan_history.csv"


def log_scan(stage, filename, result):
    row = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "stage": stage,
        "filename": filename,
        "overall_similarity": result.overall_score,
        "skill_coverage_pct": result.skill_coverage_pct,
        "combined_score": result.combined_score,
    }
    df = pd.DataFrame([row])
    header_needed = not os.path.exists(HISTORY_FILE)
    df.to_csv(HISTORY_FILE, mode="a", header=header_needed, index=False)


def score_gauge(label, value):
    st.metric(label, f"{value:.1f} / 100")
    st.progress(min(int(value), 100))


st.title("📄 Pre-Post Resume Screening & Feedback System")
st.caption(
    "Upload a job description once, then screen your resume before and after revising it "
    "to see exactly how much your changes improved your match score."
)

with st.sidebar:
    st.header("1. Job Description")
    jd_input_mode = st.radio("How would you like to provide the job description?", ["Paste text", "Upload file"])
    jd_text = ""
    if jd_input_mode == "Paste text":
        jd_text = st.text_area("Paste the job description here", height=250)
    else:
        jd_file = st.file_uploader("Upload job description (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"], key="jd_file")
        if jd_file is not None:
            jd_text = extract_text(jd_file)

    st.markdown("---")
    st.caption(
        "Tip: use the exact job posting text, not a summary — the scorer looks for the "
        "specific wording recruiters and ATS tools filter on."
    )

tab_pre, tab_post, tab_history = st.tabs(["① First Screen (Pre)", "② Re-Screen After Editing (Post)", "📊 Scan History"])

# ---------- PRE TAB ----------
with tab_pre:
    st.subheader("Upload your current resume")
    pre_file = st.file_uploader("Resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"], key="pre_resume")

    if st.button("Score this resume", key="score_pre"):
        if not jd_text.strip():
            st.error("Please provide a job description in the sidebar first.")
        elif pre_file is None:
            st.error("Please upload a resume to score.")
        else:
            with st.spinner("Scoring..."):
                resume_text = extract_text(pre_file)
                result = score_resume(resume_text, jd_text)
                tips = generate_feedback(resume_text, result)
                log_scan("pre", pre_file.name, result)

            st.session_state["pre_result"] = result
            st.session_state["pre_resume_text"] = resume_text
            st.session_state["pre_filename"] = pre_file.name

    if "pre_result" in st.session_state:
        result = st.session_state["pre_result"]
        st.success(f"Scored: {st.session_state['pre_filename']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            score_gauge("Overall Match Score", result.combined_score)
        with col2:
            score_gauge("Semantic Similarity", result.overall_score)
        with col3:
            score_gauge("Skill Keyword Coverage", result.skill_coverage_pct)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**✅ Matched skills**")
            st.write(", ".join(result.matched_skills) if result.matched_skills else "None found")
        with c2:
            st.markdown("**❌ Missing skills**")
            st.write(", ".join(result.missing_skills) if result.missing_skills else "None — great coverage")

        st.markdown("### Feedback")
        for tip in generate_feedback(st.session_state["pre_resume_text"], result):
            st.warning(tip)

        st.info("Now revise your resume based on the feedback above, then go to the second tab to re-check it.")

# ---------- POST TAB ----------
with tab_post:
    st.subheader("Upload your revised resume")
    if "pre_result" not in st.session_state:
        st.warning("Score your original resume in the first tab before comparing a revised version.")
    else:
        post_file = st.file_uploader("Revised resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"], key="post_resume")

        if st.button("Re-score this resume", key="score_post"):
            if not jd_text.strip():
                st.error("Please provide a job description in the sidebar first.")
            elif post_file is None:
                st.error("Please upload your revised resume.")
            else:
                with st.spinner("Scoring..."):
                    resume_text = extract_text(post_file)
                    post_result = score_resume(resume_text, jd_text)
                    log_scan("post", post_file.name, post_result)

                st.session_state["post_result"] = post_result
                st.session_state["post_resume_text"] = resume_text
                st.session_state["post_filename"] = post_file.name

        if "post_result" in st.session_state:
            pre_result = st.session_state["pre_result"]
            post_result = st.session_state["post_result"]
            comparison = compare_scores(pre_result, post_result)

            st.success(f"Scored: {st.session_state['post_filename']}")

            colA, colB, colC = st.columns(3)
            colA.metric("Score Before", f"{comparison['score_before']:.1f}")
            colB.metric("Score After", f"{comparison['score_after']:.1f}", delta=f"{comparison['delta']:.1f}")
            colC.metric("Skills Gained", len(comparison["skills_gained"]))

            if comparison["delta"] > 0:
                st.success(f"Your resume improved by {comparison['delta']:.1f} points. Nice work.")
            elif comparison["delta"] == 0:
                st.info("No change in score — the revision didn't add any new matched keywords or improve similarity.")
            else:
                st.error("Your score went down. Double-check that you didn't remove relevant content.")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🎯 New skills you added**")
                st.write(", ".join(comparison["skills_gained"]) if comparison["skills_gained"] else "None")
            with c2:
                st.markdown("**⚠️ Still missing**")
                st.write(", ".join(comparison["still_missing"]) if comparison["still_missing"] else "None — full coverage")

            st.markdown("### Updated Feedback")
            for tip in generate_feedback(st.session_state["post_resume_text"], post_result):
                st.warning(tip)

# ---------- HISTORY TAB ----------
with tab_history:
    st.subheader("All scans this session (stored locally in scan_history.csv)")
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No scans recorded yet.")
