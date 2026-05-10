# jobs.py
import os

import mysql.connector
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from auth import roles_required
from cosine_matcher import cosine_match_jobs

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


def get_score_from_match(match):
    return (
        match.get("match_score")
        or match.get("similarity_score")
        or match.get("cosine_score")
        or match.get("similarity")
        or match.get("score")
        or 0
    )


# ---------------------------------------------------------------------------
# Job Search
# ---------------------------------------------------------------------------
@jobs_bp.get("/api/jobs/search")
@roles_required("student")
def search_jobs():
    user_id = int(get_jwt_identity())

    keyword = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    job_type = request.args.get("type", "").strip().lower()
    skill = request.args.get("skill", "").strip()
    salary_min = request.args.get("salary_min", type=int)
    limit = min(request.args.get("limit", 20, type=int), 100)
    offset = request.args.get("offset", 0, type=int)

    db = get_db()

    try:
        cur = db.cursor(dictionary=True)

        query = """
            SELECT DISTINCT
                j.id,
                j.title,
                j.company,
                j.city,
                j.country,
                j.is_remote,
                j.apply_link,
                j.description,
                j.keywords,
                j.salary_text,
                j.salary_min,
                j.salary_max,
                j.salary_currency,
                j.salary_period
            FROM jobs j
            LEFT JOIN job_skills s ON s.job_id = j.id
            WHERE 1=1
        """
        params = []

        if keyword:
            query += """
                AND (
                    j.title LIKE %s
                    OR j.description LIKE %s
                    OR j.keywords LIKE %s
                )
            """
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        if location:
            query += " AND (j.city LIKE %s OR j.country LIKE %s)"
            loc = f"%{location}%"
            params.extend([loc, loc])

        if job_type in ("remote", "work from home"):
            query += " AND j.is_remote = 1"
        elif job_type in ("onsite", "on-site", "office"):
            query += " AND j.is_remote = 0"

        if skill:
            query += " AND LOWER(s.skill) = %s"
            params.append(skill.lower())

        if salary_min:
            query += " AND j.salary_max >= %s"
            params.append(salary_min)

        query += " ORDER BY j.id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cur.execute(query, params)
        jobs = cur.fetchall()

    finally:
        db.close()

    scored_matches = cosine_match_jobs(user_id=user_id, limit=500)

    score_map = {}
    for match in scored_matches:
        match_id = match.get("id") or match.get("job_id")
        if match_id:
            score_map[int(match_id)] = match

    for job in jobs:
        scored = score_map.get(int(job["id"]))

        job["match_score"] = get_score_from_match(scored) if scored else 0
        job["preference_score"] = 0.5

    return jsonify({
        "ok": True,
        "count": len(jobs),
        "jobs": jobs
    })


# ---------------------------------------------------------------------------
# Resume-based Matches
# ---------------------------------------------------------------------------
@jobs_bp.get("/api/jobs/matches")
@roles_required("student")
def get_matches():
    user_id = int(get_jwt_identity())
    limit = min(request.args.get("limit", 10, type=int), 50)

    matches = cosine_match_jobs(user_id=user_id, limit=limit)

    return jsonify({
        "ok": True,
        "matches": matches
    })


# ---------------------------------------------------------------------------
# Single Job Detail
# ---------------------------------------------------------------------------
@jobs_bp.get("/api/jobs/<int:job_id>")
def get_job(job_id):
    db = get_db()

    try:
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM jobs WHERE id=%s LIMIT 1", (job_id,))
        job = cur.fetchone()

        if not job:
            return jsonify({"ok": False, "error": "Not found"}), 404

        cur.execute("SELECT skill FROM job_skills WHERE job_id=%s", (job_id,))
        job["skills"] = [r["skill"] for r in cur.fetchall()]

        cur.execute("SELECT degree FROM job_degrees WHERE job_id=%s", (job_id,))
        job["degrees"] = [r["degree"] for r in cur.fetchall()]

        cur.execute("SELECT cert FROM job_certs WHERE job_id=%s", (job_id,))
        job["certifications"] = [r["cert"] for r in cur.fetchall()]

    finally:
        db.close()

    return jsonify({
        "ok": True,
        "job": job
    })