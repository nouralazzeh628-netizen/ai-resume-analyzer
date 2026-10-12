"""A small, local-first resume analyzer built with Streamlit."""

import io
import re
from collections import Counter

import streamlit as st


SKILL_ALIASES = {
    "python": ["python", "python3"],
    "sql": ["sql", "mysql", "postgresql", "postgres", "sqlite"],
    "data analysis": ["data analysis", "data analytics", "data analyst"],
    "machine learning": ["machine learning", "ml", "scikit-learn", "sklearn"],
    "deep learning": ["deep learning", "pytorch", "tensorflow", "keras"],
    "nlp": ["nlp", "natural language processing", "text classification"],
    "excel": ["excel", "spreadsheets", "pivot tables"],
    "power bi": ["power bi", "powerbi", "dax"],
    "tableau": ["tableau"],
    "statistics": ["statistics", "statistical analysis", "hypothesis testing"],
    "data visualization": ["data visualization", "visualization", "matplotlib", "seaborn", "plotly"],
    "communication": ["communication", "presentation skills", "stakeholder management"],
    "project management": ["project management", "agile", "scrum", "kanban"],
    "git": ["git", "github", "version control"],
    "aws": ["aws", "amazon web services"],
    "docker": ["docker", "containers"],
    "rest api": ["rest api", "restful", "api development"],
    "java": ["java"],
    "javascript": ["javascript", "typescript"],
    "c++": ["c++", "cpp"],
    "linux": ["linux", "ubuntu", "bash", "shell scripting"],
    "software development": ["software development", "software developer", "software engineering", "software engineer"],
    "backend development": ["backend development", "back-end development", "backend developer", "back-end developer", "server-side development"],
    "application development": ["application development", "app development", "application developer", "app developer"],
}


def extract_text(uploaded_file):
    """Extract text from PDF or DOCX uploads. TXT is decoded directly."""
    suffix = uploaded_file.name.rsplit(".", 1)[-1].lower()
    data = uploaded_file.getvalue()
    if suffix == "txt":
        return data.decode("utf-8", errors="ignore")
    if suffix == "pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == "docx":
        from docx import Document

        document = Document(io.BytesIO(data))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    raise ValueError("Unsupported file type. Please upload a PDF, DOCX, or TXT file.")


def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def find_skills(text):
    normalized = normalize(text)
    found = set()
    for skill, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
            if re.search(pattern, normalized):
                found.add(skill)
                break
    return found


def analyze(resume_text, job_text):
    resume_skills = find_skills(resume_text)
    job_skills = find_skills(job_text)
    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)
    extra = sorted(resume_skills - job_skills)
    score = round(len(matched) / len(job_skills) * 100) if job_skills else None
    words = re.findall(r"\b[\w+#.-]+\b", resume_text)
    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "extra": extra,
        "word_count": len(words),
        "job_skill_count": len(job_skills),
    }


def suggestions(result):
    items = []
    if result["missing"]:
        items.append("If you have experience with these, add them naturally to the relevant experience or skills section: " + ", ".join(result["missing"]) + ".")
    if result["word_count"] < 250:
        items.append("The resume text is quite short. Add concrete project or work examples with outcomes and measurable results.")
    elif result["word_count"] > 1000:
        items.append("The resume text is lengthy. Consider prioritizing the most relevant experience and keeping bullets concise.")
    if not result["matched"]:
        items.append("No shared skills were detected. Check that the job description and resume text were extracted correctly, or use the text boxes to paste them.")
    if not items:
        items.append("Good keyword alignment. Strengthen the resume further by describing impact with action verbs and measurable outcomes.")
    return items


st.set_page_config(page_title="AI Resume Analyzer", page_icon="🧭", layout="wide")
st.title("🧭 AI Resume Analyzer")
st.write("Compare a resume with a job description and get a quick, transparent skills match.")
st.caption("Runs locally in your browser session. Text is analyzed with a built-in keyword matcher; no resume is sent to an AI service.")

with st.sidebar:
    st.header("How it works")
    st.markdown("1. Add a resume (PDF, DOCX, or TXT) or paste its text.\n2. Paste the target job description.\n3. Review matched and missing skills.")
    st.info("The match score measures detected skills in the job description that also appear in the resume. It is a guide, not a hiring prediction.")

left, right = st.columns(2)
with left:
    st.subheader("Resume")
    uploaded = st.file_uploader("Upload resume", type=["pdf", "docx", "txt"])
    resume_text = ""
    if uploaded:
        try:
            resume_text = extract_text(uploaded)
            st.success(f"Loaded {uploaded.name}")
        except Exception as error:
            st.error(f"Could not read this file: {error}")
    pasted_resume = st.text_area("Or paste resume text", height=210, placeholder="Paste resume text here...")
    if pasted_resume.strip():
        resume_text = pasted_resume
with right:
    st.subheader("Job description")
    job_text = st.text_area("Paste job description", height=300, placeholder="Paste the job description here...")

if st.button("Analyze match", type="primary", use_container_width=True):
    if not resume_text.strip() or not job_text.strip():
        st.warning("Add both resume text and a job description to analyze the match.")
    else:
        result = analyze(resume_text, job_text)
        st.divider()
        st.subheader("Results")
        score_col, count_col, match_col = st.columns(3)
        score_col.metric("Skills match", f"{result['score']}%" if result["score"] is not None else "N/A")
        count_col.metric("Resume words", f"{result['word_count']:,}")
        match_col.metric("Matched skills", f"{len(result['matched'])} / {result['job_skill_count']}")
        if result["score"] is not None:
            st.progress(result["score"] / 100)
        else:
            st.info("No recognized skills were found in the job description. Add more detail or extend SKILL_ALIASES in app.py.")
        matched_col, missing_col, extra_col = st.columns(3)
        with matched_col:
            st.markdown("#### ✅ Matched")
            st.write(", ".join(result["matched"]) if result["matched"] else "No matches detected")
        with missing_col:
            st.markdown("#### 🎯 Missing from resume")
            st.write(", ".join(result["missing"]) if result["missing"] else "No missing skills detected")
        with extra_col:
            st.markdown("#### ➕ Other detected skills")
            st.write(", ".join(result["extra"]) if result["extra"] else "None detected")
        st.markdown("#### Suggestions")
        for suggestion in suggestions(result):
            st.write(f"- {suggestion}")
        st.caption("Only include a skill if it accurately reflects your experience. The analyzer uses a small editable keyword list and may miss synonyms or context.")

