# app.py
# Flask server: upload UI + API endpoint to upload PDF/DOCX resumes
# After upload, it also returns quick matches based on TF-IDF keyword overlap.

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

from resume_tools import (
    ALLOWED_EXTENSIONS,
    extract_text_from_pdf,
    extract_text_from_docx,
    save_resume_to_db,
    recommend_jobs_by_keyword_overlap,  # ✅ added
)

app = Flask(__name__)

MAX_UPLOAD_MB = 5
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@app.get("/upload")
def upload_page():
    return render_template("upload.html")


@app.post("/api/resume/upload")
def upload_resume_file():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "Missing file field 'file'"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "No file selected"}), 400

    filename = secure_filename(f.filename)

    if not allowed_file(filename):
        return jsonify({"ok": False, "error": "Only .pdf and .docx supported"}), 400

    user_id = int(request.form.get("user_id", 1))
    student_id_raw = request.form.get("student_id")
    student_id = int(student_id_raw) if student_id_raw not in (None, "", "null") else None

    ext = filename.rsplit(".", 1)[1].lower()

    try:
        if ext == "pdf":
            raw_text = extract_text_from_pdf(f.stream)
        else:
            raw_text = extract_text_from_docx(f.stream)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to read file: {str(e)}"}), 400

    if not raw_text or len(raw_text.strip()) < 50:
        return jsonify({
            "ok": False,
            "error": "Extracted text is empty/too short. If this is a scanned PDF, you’ll need OCR."
        }), 400

    # ✅ save resume
    resume_id, keywords = save_resume_to_db(
        student_id=student_id,
        user_id=user_id,
        filename=filename,
        raw_text=raw_text
    )

    # ✅ quick matches using stored job keywords
    matches = recommend_jobs_by_keyword_overlap(user_id=user_id, limit=10)

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