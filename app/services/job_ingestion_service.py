# from main.py. This is the logic that injest jobs in script will use to populate the database
# =====================================================
# API HELPERS
# =====================================================
import requests
import time
import random
from flask import current_app

def get_jobs(query, pages=2):
    params = {
        "query": query,
        "country": "jm",
        "num_pages": pages,
        "date_posted": "month"
    }
    # Uses config from current_app (config.py)
    r = requests.get(
        current_app.config['SEARCH_URL'], 
        headers={
            "x-rapidapi-key": current_app.config['RAPIDAPI_KEY'],
            "x-rapidapi-host": current_app.config['RAPIDAPI_HOST']
        }, 
        params=params, 
        timeout=current_app.config.get('TIMEOUT', 60)
    )
    print("Search status:", r.status_code)
    return r.json() if r.status_code == 200 else None

def get_job_details(job_id, max_retries=3):
    for attempt in range(max_retries):
        r = requests.get(
            current_app.config['DETAILS_URL'],
            headers={
                "x-rapidapi-key": current_app.config['RAPIDAPI_KEY'],
                "x-rapidapi-host": current_app.config['RAPIDAPI_HOST']
            },
            params={"job_id": job_id, "country": "jm"},
            timeout=current_app.config.get('TIMEOUT', 60)
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
            return float(x) if x is not None else None
        except (ValueError, TypeError):
            return None

    salary_min = to_float(salary_min)
    salary_max = to_float(salary_max)

    salary_source = "details" if any([d.get("job_salary"), d.get("job_min_salary")]) else "search"

    return salary_text, salary_min, salary_max, salary_currency, salary_period, salary_source

def pick_apply_link(search_job: dict, details_row: dict | None):
    d = details_row or {}
    return (search_job.get("job_apply_link")
            or d.get("job_apply_link")
            or search_job.get("job_google_link")
            or None)
