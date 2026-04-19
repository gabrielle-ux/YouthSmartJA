# cosine_matcher.py

import os
import mysql.connector
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from text_cleaning import clean_text, EXTRA_NOISE_WORDS, TECH_NORMALIZATION

load_dotenv()

# -----------------------------
# DB CONFIG
# -----------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "youthsmart"),
    "port": int(os.getenv("DB_PORT", 3306)),
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# -----------------------------
# DB HELPERS
# -----------------------------
def get_latest_resume_text(user_id: int) -> str:
    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT raw_text
            FROM resumes
            WHERE user_id=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        return row["raw_text"] if row and row.get("raw_text") else ""
    finally:
        cur.close()
        db.close()


def get_all_jobs():
    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT id, title, company, description,
                   apply_link, salary_text,
                   salary_min, salary_max, salary_currency, salary_period
            FROM jobs
            WHERE description IS NOT NULL AND description <> ''
            """
        )
        return cur.fetchall()
    finally:
        cur.close()
        db.close()


def get_job_text(job: dict) -> str:
    """
    Build job text for matching.
    Title gets extra weight by repeating it.
    Description still matters most.
    """
    title = job.get("title", "") or ""
    description = job.get("description", "") or ""

    # repeat title to give it slightly more importance
    return f"{title} {title} {description}"


def get_job_text_by_id(job_id: int) -> str:
    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT title, description
            FROM jobs
            WHERE id=%s
            LIMIT 1
            """,
            (job_id,),
        )
        row = cur.fetchone()
        if not row:
            return ""
        return get_job_text(row)
    finally:
        cur.close()
        db.close()


# -----------------------------
# OPTIONAL SINGLE TEXT COMPARISON
# -----------------------------
def compute_tfidf_cosine(text1: str, text2: str) -> float:
    """
    Reusable TF-IDF cosine similarity between two texts.
    Still useful for one-off comparisons.
    """
    text1 = clean_text(text1)
    text2 = clean_text(text2)

    if not text1 or not text2:
        return 0.0

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=3000
    )

    tfidf = vectorizer.fit_transform([text1, text2])
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return float(score)


# -----------------------------
# IMPROVED JOB MATCHING
# -----------------------------
def cosine_match_jobs(user_id: int, limit: int = 10):
    """
    Uses ONE TF-IDF model for:
    [resume + all jobs]
    Then compares the resume vector against every job vector.
    """
    resume_text = clean_text(get_latest_resume_text(user_id))
    if not resume_text:
        return []

    jobs = get_all_jobs()
    if not jobs:
        return []

    job_texts = []
    valid_jobs = []

    for job in jobs:
        job_text = clean_text(get_job_text(job))
        if job_text:
            valid_jobs.append(job)
            job_texts.append(job_text)

    if not valid_jobs:
        return []

    corpus = [resume_text] + job_texts

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=3000
    )

    tfidf_matrix = vectorizer.fit_transform(corpus)

    resume_vector = tfidf_matrix[0:1]
    job_vectors = tfidf_matrix[1:]

    scores = cosine_similarity(resume_vector, job_vectors)[0]

    results = []

    for job, score in zip(valid_jobs, scores):
        if score > 0:
            results.append({
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "apply_link": job["apply_link"],
                "salary_text": job["salary_text"],
                "salary_min": job["salary_min"],
                "salary_max": job["salary_max"],
                "salary_currency": job["salary_currency"],
                "salary_period": job["salary_period"],
                "score": round(float(score), 4)
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
