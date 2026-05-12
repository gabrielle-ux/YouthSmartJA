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
    "user": os.getenv("DB_USER", "captain"),
    "password": os.getenv("DB_PASSWORD", "captain123"),
    "database": os.getenv("DB_NAME", "youthsmart"),
    "port": int(os.getenv("DB_PORT", 3308)),
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


def get_user_preferences(user_id: int):
    """
    Gets location preferences from users.location_preferences.

    Example:
    "Kingston,St. Andrew"
    ->
    ["kingston", "st. andrew"]
    """
    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT location_preferences
            FROM users
            WHERE id=%s
            LIMIT 1
            """,
            (user_id,),
        )

        row = cur.fetchone()

        if not row or not row.get("location_preferences"):
            return []

        prefs = row["location_preferences"].split(",")

        return [
            p.strip().lower()
            for p in prefs
            if p.strip()
        ]

    finally:
        cur.close()
        db.close()


def get_all_jobs():
    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT id,
                   title,
                   company,
                   city,
                   country,
                   is_remote,
                   description,
                   apply_link,
                   salary_text,
                   salary_min,
                   salary_max,
                   salary_currency,
                   salary_period
            FROM jobs
            WHERE description IS NOT NULL
              AND description <> ''
            """
        )

        return cur.fetchall()

    finally:
        cur.close()
        db.close()


def get_job_text(job: dict) -> str:
    """
    Build job text for matching.

    We repeat the title to slightly boost
    role importance in the vector space.
    """
    title = job.get("title", "") or ""
    description = job.get("description", "") or ""

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
# PREFERENCE SCORING
# -----------------------------
def compute_preference_score(job: dict, preferences: list) -> float:
    """
    Computes preference score between 0.0 and 1.0.

    Current logic:
    +0.5 for location match
    +0.5 for remote match
    """
    score = 0.0

    job_city = (job.get("city") or "").lower()
    job_country = (job.get("country") or "").lower()

    # location match
    for pref in preferences:
        if pref in job_city or pref in job_country:
            score += 0.5
            break

    # remote preference
    if "remote" in preferences and job.get("is_remote"):
        score += 0.5

    return min(score, 1.0)


# -----------------------------
# KEYWORD EXTRACTION
# Extracts top N keywords from a document as a space-separated string.
# This fixes document length disparity bias in cosine similarity —
# comparing 500-word resume vs 2000-word job description always
# produces low cosine regardless of shared terms.
# By extracting equal-length keyword sets from both, cosine reflects
# true skill overlap rather than document length mismatch.
# -----------------------------
def extract_top_keywords(text: str, top_n: int = 50) -> str:
    """
    Extract top N TF-IDF keywords from a single document.
    Returns them as a space-separated string for downstream vectorization.
    """
    text = clean_text(text)
    if not text:
        return ""

    vec = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
    )

    try:
        X = vec.fit_transform([text])
        terms = vec.get_feature_names_out()
        scores = X.toarray()[0]
        pairs = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
        keywords = [term for term, score in pairs if score > 0][:top_n]
        return " ".join(keywords)
    except Exception:
        return text


def keyword_cosine(text1: str, text2: str, top_n: int = 50) -> float:
    """
    Keyword-to-keyword cosine similarity.
    Extracts top N keywords from each document independently,
    then compares the two equal-length keyword sets.
    This eliminates document length disparity bias.
    """
    kw1 = extract_top_keywords(text1, top_n=top_n)
    kw2 = extract_top_keywords(text2, top_n=top_n)

    if not kw1 or not kw2:
        return 0.0

    vec = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
    )

    try:
        tfidf = vec.fit_transform([kw1, kw2])
        return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except Exception:
        return 0.0


# -----------------------------
# OPTIONAL SINGLE TEXT COMPARISON
# -----------------------------
def compute_tfidf_cosine(text1: str, text2: str) -> float:
    """
    Reusable TF-IDF cosine similarity between two texts.
    Useful for one-off comparisons.
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

    score = cosine_similarity(
        tfidf[0:1],
        tfidf[1:2]
    )[0][0]

    return float(score)


# -----------------------------
# IMPROVED JOB MATCHING
# -----------------------------
def cosine_match_jobs(user_id: int, limit: int = 10):
    """
    Uses ONE TF-IDF model for:
    [resume + all jobs]

    Final score:
    final_score =
        (0.7 * match_score)
        +
        (0.3 * preference_score)
    """

    # -----------------------------
    # Load resume
    # -----------------------------
    resume_text = clean_text(
        get_latest_resume_text(user_id)
    )

    if not resume_text:
        return []

    # -----------------------------
    # Load jobs
    # -----------------------------
    jobs = get_all_jobs()

    if not jobs:
        return []

    # -----------------------------
    # Load preferences
    # -----------------------------
    preferences = get_user_preferences(user_id)

    # -----------------------------
    # Build corpus
    # -----------------------------
    job_texts = []
    valid_jobs = []

    for job in jobs:
        job_text = clean_text(
            get_job_text(job)
        )

        if job_text:
            valid_jobs.append(job)
            job_texts.append(job_text)

    if not valid_jobs:
        return []

    corpus = [resume_text] + job_texts

    # -----------------------------
    # Extract keywords from resume
    # Fixes document length disparity — resume (~500 words) vs
    # job description (~2000 words) produces artificially low cosine.
    # Comparing equal-length keyword sets gives accurate skill overlap.
    # -----------------------------
    resume_keywords = extract_top_keywords(resume_text, top_n=50)

    # -----------------------------
    # TF-IDF Vectorization (kept for preference scoring reference)
    # -----------------------------
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=3000
    )

    tfidf_matrix = vectorizer.fit_transform(corpus)
    resume_vector = tfidf_matrix[0:1]
    job_vectors = tfidf_matrix[1:]

    raw_scores = cosine_similarity(resume_vector, job_vectors)[0]

    # -----------------------------
    # Build Results using keyword cosine
    # -----------------------------
    results = []

    for job, raw_score, job_text in zip(valid_jobs, raw_scores, job_texts):

        if raw_score > 0.08:

            # Keyword-to-keyword cosine — equal length comparison
            job_keywords = extract_top_keywords(job_text, top_n=50)
            match_score = keyword_cosine(resume_text, job_text, top_n=50)

            preference_score = compute_preference_score(
                job,
                preferences
            )

            final_score = (
                (0.7 * match_score)
                +
                (0.3 * preference_score)
            )

            results.append({
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "city": job.get("city"),
                "country": job.get("country"),
                "is_remote": bool(job.get("is_remote")),
                "apply_link": job["apply_link"],
                "salary_text": job["salary_text"],
                "salary_min": job["salary_min"],
                "salary_max": job["salary_max"],
                "salary_currency": job["salary_currency"],
                "salary_period": job["salary_period"],

                # NEW SCORES
                "match_score": round(match_score, 4),
                "preference_score": round(preference_score, 4),
                "final_score": round(final_score, 4)
            })

    # -----------------------------
    # Sort by final score
    # -----------------------------
    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return results[:limit]