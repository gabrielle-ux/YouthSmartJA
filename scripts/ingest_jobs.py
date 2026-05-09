
# =====================================================
# CORE INGESTION LOGIC
# =====================================================

import sys
import os

# Ensure the script can find the 'app' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Job, JobSkill, JobCert, JobDegree, JobExperience
from app.services.job_ingestion_service import (
    get_jobs, get_job_details, pick_apply_link, pick_salary_fields
)
from app.services.keyword_service import build_keywords_for_docs
from app.services.job_extraction import extract_job_info

app = create_app()

def run_ingestion():
    with app.app_context():
        # 1. Fetch data from API
        jobs_data = get_jobs("Dentist", pages=2)
        if not jobs_data or not jobs_data.get("data"):
            print("No jobs found.")
            return

        collected = []
        for job_row in jobs_data["data"]:
            source_id = str(job_row.get("job_id"))
            
            # Fetch details
            details_resp = get_job_details(source_id)
            details_row = details_resp["data"][0] if details_resp and details_resp.get("data") else None
            
            description = (details_row.get("job_description") if details_row else None) or job_row.get("job_description") or ""
            apply_link = pick_apply_link(job_row, details_row)
            salary_info = pick_salary_fields(job_row, details_row) # (text, min, max, cur, per, src)

            collected.append({
                "source_job_id": source_id,
                "title": job_row.get("job_title"),
                "company": job_row.get("employer_name"),
                "city": job_row.get("job_city"),
                "country": job_row.get("job_country"),
                "is_remote": bool(job_row.get("job_is_remote")),
                "description": description,
                "apply_link": apply_link,
                "salary_info": salary_info
            })
            time.sleep(1) # API Safety

        # 2. Build Keywords via TF-IDF service
        docs = [f"{x['title']} {x['description']}" for x in collected]
        keywords_per_doc = build_keywords_for_docs(docs, top_n=25)

        # 3. Save to PostgreSQL using SQLAlchemy
        for x, kws in zip(collected, keywords_per_doc):
            # Check for existing job (Upsert)
            job = Job.query.filter_by(job_source="jsearch", source_job_id=x["source_job_id"]).first()
            if not job:
                job = Job(job_source="jsearch", source_job_id=x["source_job_id"])

            job.title, job.company = x["title"], x["company"]
            job.city, job.country, job.is_remote = x["city"], x["country"], x["is_remote"]
            job.description, job.apply_link = x["description"], x["apply_link"]
            job.keywords = ",".join(kws)

            # Salary Unpacking
            job.salary_text, job.salary_min, job.salary_max, \
            job.salary_currency, job.salary_period, job.salary_source = x["salary_info"]

            db.session.add(job)
            db.session.flush()  # Gets the job.id

            # 4. Extract and update related tables (Skills, Certs, etc.)
            info = extract_job_info(x["description"])
            
            # Helper to refresh child tables
            def refresh_relation(model, values, attr_name):
                model.query.filter_by(job_id=job.id).delete()
                for val in values:
                    db.session.add(model(job_id=job.id, **{attr_name: val}))

            refresh_relation(JobSkill, info["skills"], "skill")
            refresh_relation(JobCert, info["certifications"], "cert")
            refresh_relation(JobDegree, info["degrees"], "degree")
            refresh_relation(JobExperience, info["experience"], "experience")


        db.session.commit()
        print("Successfully synced jobs to PostgreSQL ✅")

if __name__ == "__main__":
    run_ingestion()
