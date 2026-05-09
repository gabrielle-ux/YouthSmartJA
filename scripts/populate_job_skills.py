import sys
import os

# This ensures the script can see the 'app' folder even if it's sitting in 'scripts'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Job, JobSkill
from app.utils.text_processing import extract_skills_from_text

def populate_job_skills():
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Fetch only necessary fields using SQLAlchemy
            # Equivalent to: SELECT id, title, description, keywords FROM jobs...
            jobs = Job.query.with_entities(Job.id, Job.title, Job.description, Job.keywords).filter(
                Job.description.isnot(None),
                Job.description != ''
            ).all()

            # 2. Clear existing skills (Equivalent to DELETE FROM job_skills)
            db.session.query(JobSkill).delete()
            
            inserted = 0
            for job in jobs:
                combined_text = " ".join([
                    job.title or "",
                    job.description or "",
                    job.keywords or ""
                ])

                skills = extract_skills_from_text(combined_text)

                for skill_name in skills:
                    # 3. Create new JobSkill row
                    # SQLAlchemy handles 'INSERT IGNORE' behavior via primary key uniqueness
                    new_skill = JobSkill(job_id=job.id, skill=skill_name)
                    db.session.add(new_skill)
                    inserted += 1

            # 4. Commit all changes at once
            db.session.commit()

            return {
                "jobs_processed": len(jobs),
                "job_skill_rows_inserted": inserted
            }

        except Exception as e:
            db.session.rollback()
            print(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    result = populate_job_skills()
    print(result)
