# Transparent Pre/Post Resume Screener

An offline Streamlit application for comparing a resume with a job description, revising the resume, and measuring what changed. The application is a decision-support tool: it does **not** reproduce a specific employer's ATS and its score is not a hiring prediction.

## What the score means

The overall score is built from three inspectable components:

| Component | Weight | What it measures |
|---|---:|---|
| Text similarity | 15% | Word and character TF-IDF overlap between the resume and cleaned job description |
| Requirement coverage | 45% | Weighted direct matches plus limited partial credit for explicitly configured transferable evidence |
| Experience evidence | 40% | Whether matched requirements are demonstrated in professional experience rather than only listed elsewhere |

The scorer distinguishes:

- **Exact matches**: the resume uses the canonical requirement wording.
- **Accepted equivalents**: the resume uses a narrow, manually reviewed alias such as `routine immunisation` for `routine immunization`.
- **Transferable evidence**: related evidence earns partial credit, but the target requirement remains in the gap list.
- **Skills-only matches**: the term appears outside professional experience and therefore receives reduced evidence credit.

The keyword bank, aliases, weights and transferable-evidence rules are visible in `skills_data.py`. If the bank extracts no requirements from a job description, coverage is zero and the interface warns the user instead of claiming full coverage.

## Key safeguards

- Removes only conservative, whole-line job-board controls such as `Save`, `Email` and `Apply now`.
- Keeps platform- or context-specific gaps visible; related experience does not become a false direct match.
- Preserves DOCX paragraph/table reading order.
- Joins wrapped PDF/DOCX bullets before checking quantified achievements.
- Warns users to add keywords and metrics only when supported by verified experience.
- Invalidates pre/post comparisons when the job description changes.
- Keeps scan history in the current browser session instead of a shared server-side CSV file.

## Project structure

```text
resume-screener/
├── app.py              # Streamlit interface and local scan history
├── parser.py           # PDF, DOCX and TXT extraction; JD cleanup
├── scorer.py           # Transparent matching and scoring engine
├── feedback.py         # Actionable, evidence-conscious feedback
├── skills_data.py      # Skill bank, aliases, weights and transfer rules
├── tests/
│   └── test_scorer.py  # PATH-style benchmark and regression tests
├── requirements.txt
└── README.md
```

## Run the application

Python 3.10 or newer is recommended.

```bash
git clone https://github.com/nuyusuf07/resume-screener.git
cd resume-screener
python -m venv .venv
```

Activate the environment:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then install and run:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`.

## Use the pre/post workflow

1. Paste or upload the exact job description.
2. Upload the current resume in **First Screen (Pre)**.
3. Review the component scores, direct matches, evidence placement, transferable evidence and genuine gaps.
4. Revise the resume outside the app without adding unsupported claims.
5. Upload the revision in **Re-Screen After Editing (Post)**.
6. Compare the overall score, evidence score, newly matched terms and remaining gaps.

Scan results are kept only in the active Streamlit browser session and clear when the session ends. Resumes and job descriptions are processed without being sent to an external model or API.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

The regression suite checks job-board cleanup, a public-health MEL benchmark, genuine-gap preservation, evidence placement, alias reporting, unknown-domain handling and wrapped quantified bullets.

## Important limitations

- TF-IDF measures lexical similarity, not meaning in the way an embedding or language model does.
- The curated bank cannot represent every profession or every employer's screening rules.
- Requirement presence does not prove proficiency, duration, recency or eligibility.
- PDF extraction depends on embedded text; image-only/scanned PDFs need OCR, which is not included.
- Scores are useful for comparing revisions under the same methodology, not for estimating the probability of an interview.

To support another domain, extend `SKILL_BANK` and add only defensible aliases or transfer rules. Add regression tests for every material rule change so a broader match does not accidentally erase a genuine requirement gap.
