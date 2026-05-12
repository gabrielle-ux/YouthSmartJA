# Resume file parsing + keyword extraction + DB insert + quick matching against stored job keywords

import os
import mysql.connector
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from pypdf import PdfReader
from docx import Document

from text_cleaning import clean_text, EXTRA_NOISE_WORDS

load_dotenv()

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "captain",
    "password": "captain123",
    "database": "youthsmart",
    "port": 3308,
}

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def get_or_create_skill(cur, skill_name: str):
    """
    Inserts a skill if it does not exist, then returns its skill id.
    """
    skill_name = skill_name.strip().lower()

    if not skill_name:
        return None

    cur.execute(
        "INSERT IGNORE INTO skills (name) VALUES (%s)",
        (skill_name,)
    )

    cur.execute(
        "SELECT id FROM skills WHERE name=%s LIMIT 1",
        (skill_name,)
    )

    row = cur.fetchone()
    return row[0] if row else None


def save_user_skills(cur, user_id: int, keywords: list):
    """
    Links extracted resume keywords to the logged-in user.
    """
    for skill in keywords:
        skill_id = get_or_create_skill(cur, skill)

        if skill_id:
            cur.execute(
                """
                INSERT IGNORE INTO user_skills (user_id, skill_id)
                VALUES (%s, %s)
                """,
                (user_id, skill_id)
            )


def extract_keywords_single_doc(text: str, top_n: int = 40):
    """
    Keyword extraction for ONE resume doc.
    """
    text = clean_text(text)

    if not text:
        return []

    vec = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=3000
    )

    X = vec.fit_transform([text])
    terms = vec.get_feature_names_out()
    scores = X.toarray()[0]

    pairs = list(zip(terms, scores))
    pairs.sort(key=lambda x: x[1], reverse=True)

    keywords = []

    for term, score in pairs:
        if score <= 0:
            continue

        term = term.strip().lower()

        if not term:
            continue

        parts = term.split()

        if all(part in EXTRA_NOISE_WORDS for part in parts):
            continue

        if term in keywords:
            continue

        keywords.append(term)

        if len(keywords) >= top_n:
            break

    return keywords


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
    """
    Saves the uploaded resume text and extracted keywords.
    Also stores keyword/skill tags in the relational skills tables.
    """
    kws = extract_keywords_single_doc(raw_text, top_n=40)
    kws_csv = ",".join(kws)

    db = get_db()
    cur = db.cursor()

    try:
        cur.execute(
            """
            INSERT INTO resumes (student_id, filename, raw_text, keywords, user_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (student_id, filename, raw_text, kws_csv, user_id)
        )

        resume_id = cur.lastrowid

        save_user_skills(cur, user_id, kws)

        db.commit()

        return resume_id, kws

    except Exception:
        db.rollback()
        raise

    finally:
        cur.close()
        db.close()


def get_latest_resume_keywords(user_id: int) -> str:
    """
    Returns the latest uploaded resume keyword CSV for a user.
    """
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute(
            """
            SELECT COALESCE(keywords, '')
            FROM resumes
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,)
        )

        row = cur.fetchone()
        return row[0] if row else ""

    finally:
        cur.close()
        db.close()


def get_latest_resume_for_user(user_id: int):
    """
    Returns metadata and keywords for the user's latest uploaded resume.
    Used by the frontend to show whether a resume is already saved.
    """
    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT id, filename, keywords, uploaded_at
            FROM resumes
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,)
        )

        return cur.fetchone()

    finally:
        cur.close()
        db.close()


def get_user_skill_tags(user_id: int):
    """
    Returns the user's skills from the relational skills/user_skills tables.
    Useful for profile/dashboard skill badges.
    """
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute(
            """
            SELECT s.name
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.id
            WHERE us.user_id = %s
            ORDER BY s.name
            """,
            (user_id,)
        )

        return [row[0] for row in cur.fetchall()]

    finally:
        cur.close()
        db.close()


def recommend_jobs_by_keyword_overlap(user_id: int, limit: int = 10):
    """
    Quick matching using keyword overlap:
    score = (# matched resume keywords) / (# job keywords)

    Returns top jobs with score, matched keywords, and job info from the jobs table.
    """
    resume_kw_csv = get_latest_resume_keywords(user_id)
    rset = set(k.strip().lower() for k in resume_kw_csv.split(",") if k.strip())

    if not rset:
        return []

    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT id, title, company, city, country, is_remote,
                   apply_link, salary_text, salary_min, salary_max,
                   salary_currency, salary_period, keywords
            FROM jobs
            WHERE keywords IS NOT NULL AND keywords <> ''
            """
        )

        jobs = cur.fetchall()

    finally:
        cur.close()
        db.close()

    scored = []

    for j in jobs:
        jset = set(
            k.strip().lower()
            for k in (j["keywords"] or "").split(",")
            if k.strip()
        )

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
                "matched_keywords": matched[:15],
            })

    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[:limit]