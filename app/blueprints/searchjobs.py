# jobs.py
import os
import mysql.connector
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from dotenv import load_dotenv
from app.services.cosine_matcher import cosine_match_jobs
from app.blueprints.auth import roles_required

load_dotenv()

jobs_bp = Blueprint("jobs", __name__)

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "youthsmart"),
        port=int(os.getenv("DB_PORT", 3306)),
    )


# ---------------------------------------------------------------------------
# Job Search
# ---------------------------------------------------------------------------
@jobs_bp.get("/api/jobs/search")
def search_jobs():
    keyword    = request.args.get("q", "").strip()
    location   = request.args.get("location", "").strip()
    job_type   = request.args.get("type", "").strip()
    skill      = request.args.get("skill", "").strip()
    salary_min = request.args.get("salary_min", type=int)
    limit      = min(request.args.get("limit", 20, type=int), 100)
    offset     = request.args.get("offset", 0, type=int)

    db = get_db()
    cur = db.cursor(dictionary=True)

    query = """
        SELECT DISTINCT j.id, j.title, j.company, j.city, j.country,
               j.is_remote, j.apply_link, j.salary_text,
               j.salary_min, j.salary_max, j.salary_currency, j.salary_period
        FROM jobs j
        LEFT JOIN job_skills s ON s.job_id = j.id
        WHERE 1=1
    """
    params = []

    if keyword:
        query += " AND (j.title LIKE %s OR j.description LIKE %s OR j.keywords LIKE %s)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])

    if location:
        query += " AND (j.city LIKE %s OR j.country LIKE %s)"
        loc = f"%{location}%"
        params.extend([loc, loc])

    if job_type == "remote":
        query += " AND j.is_remote = 1"
    elif job_type == "onsite":
        query += " AND j.is_remote = 0"

    if skill:
        query += " AND s.skill = %s"
        params.append(skill.lower())

    if salary_min:
        query += " AND j.salary_max >= %s"
        params.append(salary_min)

    query += " ORDER BY j.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cur.execute(query, params)
    jobs = cur.fetchall()
    cur.close()
    db.close()

    return jsonify({"ok": True, "count": len(jobs), "jobs": jobs})


# ---------------------------------------------------------------------------
# Resume-based Matches
# ---------------------------------------------------------------------------
@jobs_bp.get("/api/jobs/matches")
@roles_required("student", "admin")
def get_matches():
    user_id = int(get_jwt_identity())
    limit = min(request.args.get("limit", 10, type=int), 50)
    matches = cosine_match_jobs(user_id=user_id, limit=limit)
    return jsonify({"ok": True, "matches": matches})


# ---------------------------------------------------------------------------
# Single Job Detail
# ---------------------------------------------------------------------------
@jobs_bp.get("/api/jobs/<int:job_id>")
def get_job(job_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM jobs WHERE id=%s LIMIT 1", (job_id,))
    job = cur.fetchone()
    if not job:
        cur.close()
        db.close()
        return jsonify({"ok": False, "error": "Not found"}), 404

    cur.execute("SELECT skill FROM job_skills WHERE job_id=%s", (job_id,))
    job["skills"] = [r["skill"] for r in cur.fetchall()]

    cur.execute("SELECT degree FROM job_degrees WHERE job_id=%s", (job_id,))
    job["degrees"] = [r["degree"] for r in cur.fetchall()]

    cur.execute("SELECT cert FROM job_certs WHERE job_id=%s", (job_id,))
    job["certifications"] = [r["cert"] for r in cur.fetchall()]

    cur.close()
    db.close()
    return jsonify({"ok": True, "job": job})