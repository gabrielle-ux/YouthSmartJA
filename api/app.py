# app.py
# Flask server: upload UI + API endpoint to upload PDF/DOCX resumes
# After upload, it also returns quick matches based on TF-IDF cosine similarity.

import os
from datetime import timedelta

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

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS(app, origins=["http://127.0.0.1:5000", "http://localhost:5000"])

# ---------------------------------------------------------------------------
# JWT Config
# ---------------------------------------------------------------------------
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-me")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(app)

# ---------------------------------------------------------------------------
# Token revocation check (logout support)
# ---------------------------------------------------------------------------
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return is_token_revoked(jwt_payload["jti"])

# ---------------------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------------------
app.register_blueprint(auth_bp)

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
# Skill Path — students/admin only
# ---------------------------------------------------------------------------
@app.get("/api/jobs/<int:job_id>/skill-path")
@roles_required("student", "admin")
def get_skill_path(job_id):
    user_id = int(get_jwt_identity())
    # Default target of 0.30 is calibrated for TF-IDF cosine on raw
    # resume/job text, which caps out around 0.30-0.40 for even the
    # best matches. The old default of 0.85 was aspirationally wrong
    # and meant reached_target was effectively always false.
    target_score = float(request.args.get("target_score", 0.30))

    result = recommend_skill_path_for_job(
        user_id=user_id,
        job_id=job_id,
        target_score=target_score
    )

    return jsonify({
        "ok": True,
        "result": result
    })


# ---------------------------------------------------------------------------
# Resume Upload — students/admin only
# ---------------------------------------------------------------------------
@app.post("/api/resume/upload")
@roles_required("student", "admin")
def upload_resume_file():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "Missing file field 'file'"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "No file selected"}), 400

    filename = secure_filename(f.filename)

    if not allowed_file(filename):
        return jsonify({"ok": False, "error": "Only .pdf and .docx supported"}), 400

    user_id = int(get_jwt_identity())
    student_id = user_id

    ext = filename.rsplit(".", 1)[1].lower()

    try:
        if ext == "pdf":
            raw_text = extract_text_from_pdf(f.stream)
        else:
            raw_text = extract_text_from_docx(f.stream)
    except Exception:
        return jsonify({"ok": False, "error": "Failed to read file"}), 400

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
        "matches": matches
    })


if __name__ == "__main__":
    app.run(debug=True)
