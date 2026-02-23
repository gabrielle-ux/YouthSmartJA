
# Resume file parsing + keyword extraction + DB insert + quick matching against stored job keywords

import re
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from pypdf import PdfReader
from docx import Document

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "youthsmart",
    "port": 3306,
}

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def clean_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s\+\#\.\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_keywords_single_doc(text: str, top_n: int = 40):
    """
    Keyword extraction for ONE resume doc 
    """
    text = clean_text(text)
    if not text:
        return []
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=3000)
    X = vec.fit_transform([text])
    terms = vec.get_feature_names_out()
    scores = X.toarray()[0]
    pairs = list(zip(terms, scores))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return [w for (w, sc) in pairs[:top_n] if sc > 0]


def extract_text_from_pdf(file_obj) -> str:
    reader = PdfReader(file_obj)
    out = []
    for page in reader.pages:
        out.append(page.extract_text() or "")
    return "\n".join(out).strip()


def extract_text_from_docx(file_obj) -> str:
    doc = Document(file_obj)
    parts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(parts).strip()


def save_resume_to_db(*, student_id, user_id: int, filename: str, raw_text: str):
    kws = extract_keywords_single_doc(raw_text, top_n=40)
    kws_csv = ",".join(kws)

    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO resumes (student_id, filename, raw_text, keywords, user_id)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (student_id, filename, raw_text, kws_csv, user_id)
    )
    resume_id = cur.lastrowid
    db.commit()
    cur.close()
    db.close()

    return resume_id, kws


def get_latest_resume_keywords(user_id: int) -> str:
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT COALESCE(keywords,'')
        FROM resumes
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row[0] if row else ""


def recommend_jobs_by_keyword_overlap(user_id: int, limit: int = 10):
    """
    Quick matching using keyword overlap :
    score = (# matched resume keywords) / (# job keywords)

    Returns top jobs with score, matched keywords, and job info from the jobs table.
    """
    resume_kw_csv = get_latest_resume_keywords(user_id)
    rset = set(k.strip().lower() for k in resume_kw_csv.split(",") if k.strip())
    if not rset:
        return []

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT id, title, company, city, country, is_remote,
               apply_link, salary_text, salary_min, salary_max, salary_currency, salary_period,
               keywords
        FROM jobs
        WHERE keywords IS NOT NULL AND keywords <> ''
    """)
    jobs = cur.fetchall()
    cur.close()
    db.close()

    scored = []
    for j in jobs:
        jset = set(k.strip().lower() for k in (j["keywords"] or "").split(",") if k.strip())
        if not jset:
            continue

        matched = sorted(list(rset & jset))
        score = len(matched) / len(jset) if jset else 0.0

        if score > 0:
            scored.append({
                "job_id": j["id"],
                "title": j["title"],
                "company": j["company"],
                "city": j["city"],
                "country": j["country"],
                "is_remote": bool(j["is_remote"]),
                "apply_link": j["apply_link"],
                "salary_text": j["salary_text"],
                "salary_min": j["salary_min"],
                "salary_max": j["salary_max"],
                "salary_currency": j["salary_currency"],
                "salary_period": j["salary_period"],
                "score": round(score, 4),
                "matched_keywords": matched[:15]
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]