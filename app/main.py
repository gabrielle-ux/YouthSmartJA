# main.py
# Job ingestion script: RapidAPI -> MySQL (jobs + salary + apply links + tf-idf keywords + extracted fields)

import re
import requests
import time
import random
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer



def clean_text(s):
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s\+\#\.\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s



# TF-IDF (CORPUS-BASED)

def build_keywords_for_docs(docs, top_n=25):
    cleaned_docs = [clean_text(d) for d in docs]
    if not any(cleaned_docs):
        return [[] for _ in docs]

    vec = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000
    )
    X = vec.fit_transform(cleaned_docs)
    terms = vec.get_feature_names_out()

    keywords_list = []
    for i in range(X.shape[0]):
        row = X.getrow(i).toarray()[0]
        idx = row.argsort()[::-1][:top_n]
        kws = [terms[j] for j in idx if row[j] > 0]
        keywords_list.append(kws)

    return keywords_list

# =====================================================
# DATABASE
# =====================================================

def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def upsert_job(cur, job_source, source_job_id, title, company, city, country,
               is_remote, apply_link, description, keywords,
               salary_text=None, salary_min=None, salary_max=None,
               salary_currency=None, salary_period=None, salary_source=None):

    sql = """
    INSERT INTO jobs (
      job_source, source_job_id, title, company, city, country, is_remote,
      apply_link, description, keywords,
      salary_text, salary_min, salary_max, salary_currency, salary_period, salary_source
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
      title=VALUES(title),
      company=VALUES(company),
      city=VALUES(city),
      country=VALUES(country),
      is_remote=VALUES(is_remote),
      apply_link=VALUES(apply_link),
      description=VALUES(description),
      keywords=VALUES(keywords),
      salary_text=VALUES(salary_text),
      salary_min=VALUES(salary_min),
      salary_max=VALUES(salary_max),
      salary_currency=VALUES(salary_currency),
      salary_period=VALUES(salary_period),
      salary_source=VALUES(salary_source);
    """

    cur.execute(sql, (
        job_source, source_job_id, title, company, city, country, 1 if is_remote else 0,
        apply_link, description, keywords,
        salary_text, salary_min, salary_max,
        salary_currency, salary_period, salary_source
    ))

    cur.execute(
        "SELECT id FROM jobs WHERE job_source=%s AND source_job_id=%s",
        (job_source, source_job_id)
    )
    return cur.fetchone()[0]


def refresh_many_kv(cur, table, job_id, col_name, values):
    cur.execute(f"DELETE FROM {table} WHERE job_id=%s", (job_id,))
    if not values:
        return
    sql = f"INSERT INTO {table} (job_id, {col_name}) VALUES (%s, %s)"
    cur.executemany(sql, [(job_id, v) for v in values])



SKILLS = [
    "python", "java", "javascript", "typescript", "react", "node", "node.js",
    "sql", "mysql", "postgresql", "docker", "kubernetes", "aws", "azure", "gcp",
    "flask", "django", "fastapi", "spring", "spring boot", ".net", "c#", "git",
    "rest", "rest api", "graphql", "microservices",
    "excel", "communication", "accounting", "quickbooks", "sage"
]

CERT_PATTERNS = [
    r"\bPMP\b", r"\bPRINCE2\b", r"\bCISSP\b",
    r"\bSix\s*Sigma\b", r"\bLean\s*Six\s*Sigma\b"
]

DEGREE_PATTERNS = [
    r"\bBSc\b", r"\bBA\b", r"\bMBA\b",
    r"\bBachelor'?s\b", r"\bMaster'?s\b", r"\bDegree\b"
]

EXP_PATTERNS = [
    r"\b(\d{1,2})\s*(?:-|–|to)\s*(\d{1,2})\s*(?:years?|yrs?)\b",
    r"\b(\d{1,2})\+?\s*(?:years?|yrs?)\b",
    r"\b(?:minimum|min\.?|at\s+least)\s+(\d{1,2})\s*(?:years?|yrs?)\b",
    r"\b(\d{1,2})\s*(?:years?|yrs?)\s+experience\b",
]


def dedupe_keep_order(items):
    seen = set()
    out = []
    for x in items:
        key = str(x).lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(x)
    return out


def extract_info(text: str):
    if not text:
        return {"skills": [], "certifications": [], "degrees": [], "experience": []}

    found_skills = []
    for s in SKILLS:
        pattern = r"(?<!\w)" + re.escape(s) + r"(?!\w)"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found_skills.append(s)

    found_certs = []
    for p in CERT_PATTERNS:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            found_certs.append(m.group(0))

    found_degrees = []
    for p in DEGREE_PATTERNS:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            found_degrees.append(m.group(0))

    found_exp = []
    for p in EXP_PATTERNS:
        for m in re.finditer(p, text, flags=re.IGNORECASE):
            found_exp.append(m.group(0))

    return {
        "skills": dedupe_keep_order(found_skills),
        "certifications": dedupe_keep_order(found_certs),
        "degrees": dedupe_keep_order(found_degrees),
        "experience": dedupe_keep_order(found_exp),
    }


# =====================================================
# API HELPERS
# =====================================================

def get_jobs(query, pages=2):
    params = {
        "query": query,
        "country": "jm",
        "num_pages": pages,
        "date_posted": "month"
    }
    r = requests.get(URL, headers=HEADERS, params=params, timeout=TIMEOUT)
    print("Search status:", r.status_code)
    if r.status_code == 200:
        return r.json()
    print("Search error:", r.text[:200])
    return None


def get_job_details(job_id, max_retries=3):
    for attempt in range(max_retries):
        r = requests.get(
            DETAILS_URL,
            headers=HEADERS,
            params={"job_id": job_id, "country": "jm"},
            timeout=TIMEOUT
        )
        if r.status_code == 200:
            return r.json()

        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(10, (2 ** attempt) + random.random()))
            continue

        print("Details error:", r.status_code, r.text[:200])
        return None
    return None


def pick_salary_fields(search_job: dict, details_row: dict | None):
    d = details_row or {}
    salary_text = (d.get("job_salary") or search_job.get("job_salary") or None)
    salary_min = (d.get("job_min_salary") or search_job.get("job_min_salary") or None)
    salary_max = (d.get("job_max_salary") or search_job.get("job_max_salary") or None)
    salary_currency = (d.get("job_salary_currency") or search_job.get("job_salary_currency") or None)
    salary_period = (d.get("job_salary_period") or search_job.get("job_salary_period") or None)

    def to_float(x):
        try:
            if x is None:
                return None
            return float(x)
        except Exception:
            return None

    salary_min = to_float(salary_min)
    salary_max = to_float(salary_max)

    salary_source = None
    if any([d.get("job_salary"), d.get("job_min_salary"), d.get("job_max_salary")]):
        salary_source = "details"
    elif any([search_job.get("job_salary"), search_job.get("job_min_salary"), search_job.get("job_max_salary")]):
        salary_source = "search"

    return salary_text, salary_min, salary_max, salary_currency, salary_period, salary_source


def pick_apply_link(search_job: dict, details_row: dict | None):
    d = details_row or {}
    return (search_job.get("job_apply_link")
            or d.get("job_apply_link")
            or search_job.get("job_google_link")
            or None)




if __name__ == "__main__":
    jobs_data = get_jobs(" Dentist", pages=2)
    if not jobs_data:
        raise SystemExit(1)

    jobs = jobs_data.get("data", [])
    print("Jobs returned:", len(jobs))
    if not jobs:
        raise SystemExit(0)

    collected = []
    for job in jobs:
        title = job.get("job_title") or ""
        company = job.get("employer_name") or ""
        city = job.get("job_city")
        country = job.get("job_country")
        is_remote = bool(job.get("job_is_remote"))
        source_job_id = str(job.get("job_id"))

        details = get_job_details(source_job_id)
        details_row = None
        full_desc = ""

        if details and details.get("data"):
            details_row = details["data"][0]
            full_desc = details_row.get("job_description") or ""

        if not full_desc.strip():
            full_desc = job.get("job_description") or ""

        apply_link = pick_apply_link(job, details_row)
        salary_text, salary_min, salary_max, salary_currency, salary_period, salary_source = pick_salary_fields(job, details_row)

        print("\nTitle:", title)
        print("Company:", company)
        print("Apply:", (apply_link or "")[:120])
        if salary_text or salary_min or salary_max:
            print("Salary:", salary_text or f"{salary_min}-{salary_max} {salary_currency or ''} {salary_period or ''}".strip())
        else:
            print("Salary: (none listed)")

        collected.append({
            "source_job_id": source_job_id,
            "title": title,
            "company": company,
            "city": city,
            "country": country,
            "is_remote": is_remote,
            "apply_link": apply_link,
            "description": full_desc,
            "salary_text": salary_text,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": salary_currency,
            "salary_period": salary_period,
            "salary_source": salary_source
        })

    docs = [f"{x['title']} {x['description']}" for x in collected]
    keywords_per_doc = build_keywords_for_docs(docs, top_n=25)

    db = get_db()
    cur = db.cursor()

    for x, kws in zip(collected, keywords_per_doc):
        info = extract_info(x["description"])
        keywords_str = ",".join(kws)

        db_job_id = upsert_job(
            cur,
            job_source="jsearch",
            source_job_id=x["source_job_id"],
            title=x["title"],
            company=x["company"],
            city=x["city"],
            country=x["country"],
            is_remote=x["is_remote"],
            apply_link=x["apply_link"],
            description=x["description"],
            keywords=keywords_str,
            salary_text=x["salary_text"],
            salary_min=x["salary_min"],
            salary_max=x["salary_max"],
            salary_currency=x["salary_currency"],
            salary_period=x["salary_period"],
            salary_source=x["salary_source"]
        )

        refresh_many_kv(cur, "job_skills", db_job_id, "skill", info["skills"])
        refresh_many_kv(cur, "job_certs", db_job_id, "cert", info["certifications"])
        refresh_many_kv(cur, "job_degrees", db_job_id, "degree", info["degrees"])
        refresh_many_kv(cur, "job_experience", db_job_id, "experience", info["experience"])

        print(f"Saved job_id={db_job_id} | keywords={len(kws)} | skills={len(info['skills'])}")

    db.commit()
    cur.close()
    db.close()

    print("\nSaved jobs to DB ✅ (salary + apply links included)")
