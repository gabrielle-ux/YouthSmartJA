# cosine_matcher.py


import re
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------
# DB CONFIG (same as main.py)
# -----------------------------
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Happy321",
    "database": "youthsmart",
    "port": 3306,
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# -----------------------------
# CLEAN TEXT (reuse logic)
# -----------------------------
def clean_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s\+\#\.\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def cosine_match_jobs(user_id: int, limit: int = 10):
    """
    Uses TF-IDF + Cosine Similarity to match a user's resume to jobs
    """

    db = get_db()
    cur = db.cursor(dictionary=True)

    # -----------------------------
    # STEP 1: Get latest resume
    # -----------------------------
    cur.execute("""
        SELECT raw_text
        FROM resumes
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    resume_row = cur.fetchone()

    if not resume_row:
        cur.close()
        db.close()
        return []

    resume_text = clean_text(resume_row["raw_text"])

    # -----------------------------
    # STEP 2: Get jobs
    # -----------------------------
    cur.execute("""
        SELECT id, title, company, description,
               apply_link, salary_text,
               salary_min, salary_max, salary_currency, salary_period
        FROM jobs
        WHERE description IS NOT NULL AND description <> ''
    """)

    jobs = cur.fetchall()

    cur.close()
    db.close()

    if not jobs:
        return []

    # -----------------------------
    # STEP 3: Prepare documents
    # -----------------------------
    job_texts = [clean_text(j["description"]) for j in jobs]

    documents = [resume_text] + job_texts

    # -----------------------------
    # STEP 4: TF-IDF vectorization
    # -----------------------------
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000
    )

    tfidf_matrix = vectorizer.fit_transform(documents)

    # -----------------------------
    # STEP 5: Cosine similarity
    # -----------------------------
    resume_vector = tfidf_matrix[0]
    job_vectors = tfidf_matrix[1:]

    similarity_scores = cosine_similarity(resume_vector, job_vectors)[0]

    # -----------------------------
    # STEP 6: Rank jobs
    # -----------------------------
    results = []

    for i, job in enumerate(jobs):
        score = float(similarity_scores[i])

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
                "score": round(score, 4)
            })

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:limit]


# -----------------------------
# TEST RUN (optional)
# -----------------------------
if __name__ == "__main__":
    user_id = 1  # change to test user
    matches = cosine_match_jobs(user_id)

    for m in matches:
        print(f"{m['title']} ({m['company']}) → Score: {m['score']}")
