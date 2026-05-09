# app.py
# Flask server: upload UI + API endpoint to upload PDF/DOCX resumes
# After upload, it also returns quick matches based on TF-IDF cosine similarity.

import os
import requests
from datetime import timedelta
from searchjobs import jobs_bp

from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import JWTManager, get_jwt_identity
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from resume_tools import (
    ALLOWED_EXTENSIONS,
    extract_text_from_pdf,
    extract_text_from_docx,
    save_resume_to_db,
)

from cosine_matcher import cosine_match_jobs
from skill_path_tools import recommend_skill_path_for_job
from auth import auth_bp, is_token_revoked, roles_required

from bookmark_tools import (
    save_bookmark,
    get_user_bookmarks,
    delete_bookmark,
)

load_dotenv()

# ---------------------------------------------------------------------------
# n8n Webhook URL
# Production URL from your active n8n workflow
# ---------------------------------------------------------------------------
N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/guidance-courses"
)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS(
    app,
    resources={r"/api/*": {"origins": [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5000",
        "http://localhost:5000",
    ]}},
    supports_credentials=True,
)

# ---------------------------------------------------------------------------
# JWT Config
# ---------------------------------------------------------------------------
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-me")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(app)

# ---------------------------------------------------------------------------
# Token revocation check
# ---------------------------------------------------------------------------
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return is_token_revoked(jwt_payload["jti"])


# ---------------------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(jobs_bp)

# ---------------------------------------------------------------------------
# Upload Config
# ---------------------------------------------------------------------------
MAX_UPLOAD_MB = 5
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Auth Test Page
# ---------------------------------------------------------------------------
@app.get("/auth-test")
def auth_test():
    return render_template("auth_test.html")


# ---------------------------------------------------------------------------
# Upload Page
# ---------------------------------------------------------------------------
@app.get("/upload")
def upload_page():
    return render_template("upload.html")


# ---------------------------------------------------------------------------
# Job Matches Feed — students/admin only
# ---------------------------------------------------------------------------
@app.get("/api/jobs/matches")
@roles_required("student", "admin")
def get_job_matches():
    user_id = int(get_jwt_identity())

    matches = cosine_match_jobs(user_id=user_id, limit=10)

    return jsonify({
        "ok": True,
        "matches": matches
    })


# ---------------------------------------------------------------------------
# Save Bookmark — students/admin only
# ---------------------------------------------------------------------------
@app.post("/api/bookmarks")
@roles_required("student", "admin")
def create_bookmark():
    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    job_id = data.get("job_id")
    match_score = data.get("match_score", 0)
    pref_score = data.get("preference_score", 0)
    final_score = data.get("final_score", 0)

    if not job_id:
        return jsonify({
            "ok": False,
            "error": "job_id is required"
        }), 400

    save_bookmark(
        user_id=user_id,
        job_id=job_id,
        match_score=match_score,
        pref_score=pref_score,
        final_score=final_score
    )

    return jsonify({
        "ok": True,
        "message": "Bookmark saved"
    })


# ---------------------------------------------------------------------------
# Get Bookmarks — students/admin only
# ---------------------------------------------------------------------------
@app.get("/api/bookmarks")
@roles_required("student", "admin")
def get_bookmarks():
    user_id = int(get_jwt_identity())

    bookmarks = get_user_bookmarks(user_id)

    return jsonify({
        "ok": True,
        "bookmarks": bookmarks
    })


# ---------------------------------------------------------------------------
# Delete Bookmark — students/admin only
# ---------------------------------------------------------------------------
@app.delete("/api/bookmarks/<int:job_id>")
@roles_required("student", "admin")
def remove_bookmark(job_id):
    user_id = int(get_jwt_identity())

    deleted = delete_bookmark(user_id, job_id)

    if deleted == 0:
        return jsonify({
            "ok": False,
            "error": "Bookmark not found"
        }), 404

    return jsonify({
        "ok": True,
        "message": "Bookmark deleted"
    })


# ---------------------------------------------------------------------------
# Skill Path — students/admin only
# ---------------------------------------------------------------------------
@app.get("/api/jobs/<int:job_id>/skill-path")
@roles_required("student", "admin")
def get_skill_path(job_id):
    user_id = int(get_jwt_identity())

    target_score = float(request.args.get("target_score", 0.30))

    result = recommend_skill_path_for_job(
        user_id=user_id,
        job_id=job_id,
        target_score=target_score
    )

    # Return both nested and direct fields so frontend can read it easily.
    return jsonify({
        "ok": True,
        "result": result,
        **result
    })


# ---------------------------------------------------------------------------
# Guidance Courses — students/admin only
# Combines Dijkstra skill path + n8n course recommendations
# ---------------------------------------------------------------------------
@app.get("/api/jobs/<int:job_id>/guidance-courses")
@roles_required("student", "admin")
def get_guidance_courses(job_id):
    user_id = int(get_jwt_identity())

    target_score = float(request.args.get("target_score", 0.30))

    # 1. Generate skill path using your Dijkstra-style algorithm
    skill_path_result = recommend_skill_path_for_job(
        user_id=user_id,
        job_id=job_id,
        target_score=target_score
    )

    # 2. Extract skills from the Dijkstra path
    skills = [
        step["learn"]
        for step in skill_path_result.get("path", [])
        if step.get("learn")
    ]

    # 3. Fallback to missing_skills if path is empty
    if not skills:
        skills = skill_path_result.get("missing_skills", [])

    # 4. If no skills are missing, return clean response
    if not skills:
        return jsonify({
            "ok": True,
            "message": "No missing skills found for this job.",
            "skill_path": skill_path_result,
            "courses": [],
            "n8n": {
                "ok": True,
                "courses": []
            }
        })

    # 5. Send missing skills to n8n
    try:
        n8n_response = requests.post(
            N8N_WEBHOOK_URL,
            json={
                "user_id": user_id,
                "job_id": job_id,
                "missing_skills": skills,
                "skills": skills
            },
            timeout=15
        )

        n8n_response.raise_for_status()
        n8n_data = n8n_response.json()

    except requests.RequestException as exc:
        return jsonify({
            "ok": False,
            "error": "Failed to connect to n8n workflow.",
            "details": str(exc),
            "skill_path": skill_path_result,
            "courses": []
        }), 502

    # 6. Extract courses from n8n response
    courses = (
        n8n_data.get("courses")
        or n8n_data.get("recommendations")
        or []
    )

    # 7. Return data in a frontend-friendly format
    return jsonify({
        "ok": True,
        "skill_path": skill_path_result,
        "missing_skills": skills,
        "courses": courses,
        "n8n": n8n_data
    })


# ---------------------------------------------------------------------------
# Resume Upload — students/admin only
# ---------------------------------------------------------------------------
@app.post("/api/resume/upload")
@roles_required("student", "admin")
def upload_resume_file():
    if "file" not in request.files:
        return jsonify({
            "ok": False,
            "error": "Missing file field 'file'"
        }), 400

    f = request.files["file"]

    if not f or not f.filename:
        return jsonify({
            "ok": False,
            "error": "No file selected"
        }), 400

    filename = secure_filename(f.filename)

    if not allowed_file(filename):
        return jsonify({
            "ok": False,
            "error": "Only .pdf and .docx supported"
        }), 400

    user_id = int(get_jwt_identity())
    student_id = user_id

    ext = filename.rsplit(".", 1)[1].lower()

    try:
        if ext == "pdf":
            raw_text = extract_text_from_pdf(f.stream)
        else:
            raw_text = extract_text_from_docx(f.stream)
    except Exception:
        return jsonify({
            "ok": False,
            "error": "Failed to read file"
        }), 400

    if not raw_text or len(raw_text.strip()) < 50:
        return jsonify({
            "ok": False,
            "error": "Extracted text is empty/too short. If this is a scanned PDF, you'll need OCR."
        }), 400

    resume_id, keywords = save_resume_to_db(
        student_id=student_id,
        user_id=user_id,
        filename=filename,
        raw_text=raw_text
    )

    matches = cosine_match_jobs(user_id=user_id, limit=10)

    return jsonify({
        "ok": True,
        "resume_id": resume_id,
        "filename": filename,
        "text_length": len(raw_text),
        "keywords_preview": keywords[:20],
        "keywords": keywords,
        "matches": matches
    })


if __name__ == "__main__":
    app.run(debug=True)