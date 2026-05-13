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
    if not match:
        return 0

    return (
        match.get("match_score")
        or match.get("similarity_score")
        or match.get("cosine_score")
        or match.get("similarity")
        or match.get("score")
        or 0
    )


def calculate_preference_score(job, career_area="", skill="", work_style=""):
    score = 0.0

    text = f"""
        {job.get("title") or ""}
        {job.get("company") or ""}
        {job.get("description") or ""}
        {job.get("keywords") or ""}
    """.lower()

    if career_area and career_area.lower() in text:
        score += 0.4

    if skill and skill.lower() in text:
        score += 0.4

    work_style = work_style.lower()

    if work_style == "remote" and job.get("is_remote"):
        score += 0.2

    elif work_style in ("on-site", "onsite") and not job.get("is_remote"):
        score += 0.2

    elif work_style == "hybrid" and "hybrid" in text:
        score += 0.2

    return round(min(score, 1.0), 2)


# ---------------------------------------------------------------------------
# Job Search
# ---------------------------------------------------------------------------
@jobs_bp.get("/api/jobs/search")
@roles_required("student")
def search_jobs():
    user_id = int(get_jwt_identity())

    keyword = request.args.get("q", "").strip()

    # New frontend filters
    career_area = request.args.get("career_area", "").strip().lower()
    skill = request.args.get("skill", "").strip().lower()
    work_style = request.args.get("work_style", "").strip().lower()

    # Older filters kept so old frontend calls do not break
    location = request.args.get("location", "").strip()
    job_type = request.args.get("type", "").strip().lower()
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

        # Search bar
        if keyword:
            kw = f"%{keyword.lower()}%"
            query += """
                AND (
                    LOWER(j.title) LIKE %s
                    OR LOWER(j.description) LIKE %s
                    OR LOWER(j.keywords) LIKE %s
                )
            """
            params.extend([kw, kw, kw])

        # Career Area dropdown
        if career_area:
            ca = f"%{career_area}%"
            query += """
                AND (
                    LOWER(j.title) LIKE %s
                    OR LOWER(j.description) LIKE %s
                    OR LOWER(j.keywords) LIKE %s
                )
            """
            params.extend([ca, ca, ca])

        # Skill dropdown
        if skill:
            query += """
                AND (
                    LOWER(s.skill) = %s
                    OR LOWER(j.title) LIKE %s
                    OR LOWER(j.description) LIKE %s
                    OR LOWER(j.keywords) LIKE %s
                )
            """
            skill_like = f"%{skill}%"
            params.extend([skill, skill_like, skill_like, skill_like])

        # Work Style dropdown
        if work_style == "remote":
            query += " AND j.is_remote = 1"

        elif work_style in ("on-site", "onsite"):
            query += " AND j.is_remote = 0"

        elif work_style == "hybrid":
            query += """
                AND (
                    LOWER(j.description) LIKE %s
                    OR LOWER(j.keywords) LIKE %s
                    OR LOWER(j.title) LIKE %s
                )
            """
            params.extend(["%hybrid%", "%hybrid%", "%hybrid%"])

        # Old location filter support
        if location:
            loc = f"%{location}%"
            query += " AND (j.city LIKE %s OR j.country LIKE %s)"
            params.extend([loc, loc])

        # Old type filter support
        if job_type in ("remote", "work from home"):
            query += " AND j.is_remote = 1"

        elif job_type in ("onsite", "on-site", "office"):
            query += " AND j.is_remote = 0"

        # Old salary filter support
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

        job["match_score"] = get_score_from_match(scored)
        job["preference_score"] = calculate_preference_score(
            job,
            career_area=career_area,
            skill=skill,
            work_style=work_style,
        )

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