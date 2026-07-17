# Pre-Post Resume Screening and Feedback System

A working implementation of the system described in the project proposal. It scores a resume
against a job description, gives specific feedback on what's missing, and then lets you
re-score a revised version to see exactly how much your changes improved your match.

No external AI model downloads or API keys are required — it runs fully offline using
TF-IDF/cosine similarity (scikit-learn) for semantic matching and a curated keyword bank
for skill-coverage checks. This matters for a project defence on a lab machine that might
not have reliable internet on the day.

## 1. Project structure

```
resume_screener/
├── app.py                  # Streamlit web interface (run this)
├── parser.py                # Extracts text from PDF / DOCX / TXT resumes
├── scorer.py                # TF-IDF similarity + skill-keyword matching engine
├── feedback.py               # Turns scores into plain-language, actionable feedback
├── skills_data.py             # Curated skill/keyword bank (edit this to add more skills)
├── requirements.txt
├── sample_data/
│   ├── sample_job_description.txt
│   ├── sample_resume_v1_before.txt
│   ├── sample_resume_v2_after.txt
│   └── demo_run_output.txt    # Real output from running the pipeline on the samples
└── README.md
```

## 2. How to run it

```bash
cd resume_screener
pip install -r requirements.txt
streamlit run app.py
```

This opens the app in your browser (usually `http://localhost:8501`). If it doesn't open
automatically, copy the "Local URL" printed in the terminal into your browser.

## 3. How to use it

1. **Sidebar** — paste or upload the job description you're targeting.
2. **Tab ① First Screen (Pre)** — upload your current resume. You'll get:
   - An overall match score out of 100
   - A semantic similarity score (how closely your resume's wording matches the JD)
   - A skill-keyword coverage score
   - A list of matched vs. missing skills
   - Plain-language feedback (missing keywords, weak/short resume, no measurable
     achievements, missing contact info, etc.)
3. Revise your resume outside the app based on that feedback.
4. **Tab ② Re-Screen After Editing (Post)** — upload the revised resume against the same
   job description. You'll see a before/after comparison: score delta, skills gained,
   and what's still missing.
5. **Tab 📊 Scan History** — every scan (pre and post) is logged locally to
   `scan_history.csv` with a timestamp, so you can track multiple attempts over time.

## 4. Sample test run (already verified working)

`sample_data/` contains a sample job description and two versions of a resume — a weak
first draft and a revised version — so you can test the system immediately without
needing your own files. Running the scoring pipeline directly on these (not through the
UI — this is the raw engine output, captured in `sample_data/demo_run_output.txt`) gives:

| Metric | Before | After | Change |
|---|---|---|---|
| Overall Match Score | 8.5 / 100 | 42.9 / 100 | **+34.4** |
| Semantic Similarity | 9.4 / 100 | 28.6 / 100 | +19.2 |
| Skill Coverage | 7.1% | 64.3% | +57.2% |
| Matched skills | `python` only | `communication, machine learning, pandas, power bi, python, rest api, sql, statistics, teamwork` | +8 skills |

This is the exact "before → feedback → revise → after" loop the proposal describes,
running on real (if small) sample data rather than a hypothetical example.

To reproduce it yourself: upload `sample_resume_v1_before.txt` in Tab ①, then
`sample_resume_v2_after.txt` in Tab ②, using `sample_job_description.txt` as the job
description in the sidebar.

## 5. Notes for the project report / defence

- **Why TF-IDF instead of a transformer/embedding model?** Sentence-embedding models
  (e.g. Sentence-BERT) generally give richer semantic matching, but they require
  downloading multi-hundred-MB model weights from the internet the first time they run.
  TF-IDF + cosine similarity has no such dependency, is well-documented in the reviewed
  literature (Saatçı et al., 2024; Khatri et al., 2025) as a legitimate baseline approach,
  and is something you can fully explain line-by-line in a viva. If you want to extend
  the project, swapping in `sentence-transformers` is a natural "future work" section —
  the `scorer.py` module is written so that swap only touches `_tfidf_similarity()`.
- **Why a keyword bank instead of NER (Named Entity Recognition)?** Same reasoning —
  spaCy's pretrained NER models also require a model download. The keyword bank in
  `skills_data.py` is easy to extend (just add strings to the relevant list) and easy to
  defend: you can point to the exact list of terms being matched.
- **Extending the skill bank**: if you're tailoring this toward specific roles (e.g. GIS
  or health-data roles), add relevant terms to `skills_data.py` — there's already a
  `gis_geospatial` category started as an example.
- **Known limitation to mention in your report**: keyword matching won't catch a skill
  described with completely different wording than the job description (e.g. "R" vs
  "statistical programming"). This is exactly the gap that swapping in a semantic
  embedding model would close — a good place to discuss trade-offs in your report.
