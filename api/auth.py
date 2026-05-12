import os
import re
from functools import wraps

import bcrypt
import mysql.connector
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
)

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "captain"),
    "password": os.getenv("DB_PASSWORD", "captain123"),
    "database": os.getenv("DB_NAME", "youthsmart"),
    "port": int(os.getenv("DB_PORT", 3308)),
}

JAMAICAN_PARISHES = {
    "Kingston", "St. Andrew", "St. Thomas", "Portland",
    "St. Mary", "St. Ann", "Trelawny", "St. James",
    "Hanover", "Westmoreland", "St. Elizabeth",
    "Manchester", "Clarendon", "St. Catherine",
}

EMAIL_PATTERN = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def json_error(message: str, status: int):
    return jsonify({"ok": False, "error": message}), status


def validate_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email))


def validate_password(password: str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must include at least one number"
    return True, ""


def validate_parishes(parishes: list):
    invalid = [p for p in parishes if p not in JAMAICAN_PARISHES]
    if invalid:
        return False, f"Invalid parish(es): {', '.join(invalid)}"
    return True, ""


def blocklist_token(jti: str):
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute("INSERT IGNORE INTO token_blocklist (jti) VALUES (%s)", (jti,))
        db.commit()
    finally:
        db.close()


def is_token_revoked(jti: str) -> bool:
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute("SELECT id FROM token_blocklist WHERE jti=%s LIMIT 1", (jti,))
        return cur.fetchone() is not None
    finally:
        db.close()


def get_current_user_id() -> int:
    return int(get_jwt_identity())


def get_current_user_role() -> str:
    return get_jwt().get("role", "student")


def roles_required(*allowed_roles):
    def outer(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            verify_jwt_in_request()
            role = get_current_user_role()
            if role not in allowed_roles:
                return json_error("Access denied", 403)
            return fn(*args, **kwargs)
        return inner
    return outer


def get_user_by_email(email: str):
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, email, password_hash, full_name, role,
                   COALESCE(is_active, 1) AS is_active
            FROM users
            WHERE email=%s
            LIMIT 1
            """,
            (email,),
        )
        return cur.fetchone()
    finally:
        db.close()


def get_user_by_id(user_id: int):
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, email, full_name, age, bio, parish,
                   location_preferences,
                   career_interest, preferred_job_type, work_style,
                   availability, learning_goals,
                   role,
                   COALESCE(is_active, 1) AS is_active,
                   created_at, updated_at
            FROM users
            WHERE id=%s
            LIMIT 1
            """,
            (user_id,),
        )
        return cur.fetchone()
    finally:
        db.close()


auth_bp = Blueprint("auth", __name__)


# ---------------- REGISTER ----------------
@auth_bp.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    full_name = data.get("full_name", "").strip()
    role = data.get("role", "student").strip().lower()

    career_interest = data.get("career_interest", "").strip()
    preferred_job_type = data.get("preferred_job_type", "").strip()
    work_style = data.get("work_style", "").strip()
    availability = data.get("availability", "").strip()
    learning_goals = data.get("learning_goals", "").strip()

    if not email or not password or not full_name:
        return json_error("full_name, email, and password are required", 400)

    if not validate_email(email):
        return json_error("Invalid email format", 400)

    valid_pw, pw_err = validate_password(password)
    if not valid_pw:
        return json_error(pw_err, 400)

    if role not in ("student", "employer", "admin"):
        return json_error("Invalid role", 400)

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    db = get_db()
    try:
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO users (
                email, password_hash, full_name, role,
                career_interest, preferred_job_type, work_style,
                availability, learning_goals
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                email, password_hash, full_name, role,
                career_interest, preferred_job_type, work_style,
                availability, learning_goals,
            ),
        )
        db.commit()
        user_id = cur.lastrowid
    except mysql.connector.IntegrityError:
        return json_error("Email already registered", 409)
    finally:
        db.close()

    token = create_access_token(identity=str(user_id), additional_claims={"role": role})

    return jsonify({
        "ok": True,
        "user": {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role": role,
            "career_interest": career_interest,
            "preferred_job_type": preferred_job_type,
            "work_style": work_style,
            "availability": availability,
            "learning_goals": learning_goals,
        },
        "access_token": token
    }), 201


# ---------------- LOGIN ----------------
@auth_bp.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return json_error("Email and password are required", 400)

    user = get_user_by_email(email)
    if not user:
        return json_error("Invalid email or password", 401)

    if not user["is_active"]:
        return json_error("Account disabled", 403)

    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return json_error("Invalid email or password", 401)

    token = create_access_token(identity=str(user["id"]), additional_claims={"role": user["role"]})

    return jsonify({
        "ok": True,
        "user": user,
        "access_token": token
    })


# ---------------- LOGOUT ----------------
@auth_bp.post("/api/auth/logout")
@jwt_required()
def logout():
    blocklist_token(get_jwt()["jti"])
    return jsonify({"ok": True})


# ---------------- ME ----------------
@auth_bp.get("/api/auth/me")
@jwt_required()
def me():
    user = get_user_by_id(get_current_user_id())
    if not user:
        return json_error("User not found", 404)

    if user.get("created_at"):
        user["created_at"] = str(user["created_at"])
    if user.get("updated_at"):
        user["updated_at"] = str(user["updated_at"])

    return jsonify({"ok": True, "user": user})


# ---------------- PROFILE ----------------
@auth_bp.put("/api/auth/profile")
@jwt_required()
def update_profile():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    if not data:
        return json_error("Missing JSON body", 400)

    fields = {}

    if "full_name" in data:
        fields["full_name"] = data["full_name"].strip()

    if "age" in data:
        age = data["age"]
        if not isinstance(age, int) or not (13 <= age <= 100):
            return json_error("Invalid age", 400)
        fields["age"] = age

    if "bio" in data:
        fields["bio"] = data["bio"]

    if "parish" in data:
        if data["parish"] not in JAMAICAN_PARISHES:
            return json_error("Invalid parish", 400)
        fields["parish"] = data["parish"]

    if "location_preferences" in data:
        valid, err = validate_parishes(data["location_preferences"])
        if not valid:
            return json_error(err, 400)
        fields["location_preferences"] = ",".join(data["location_preferences"])

    if "career_interest" in data:
        fields["career_interest"] = data["career_interest"].strip()

    if "preferred_job_type" in data:
        fields["preferred_job_type"] = data["preferred_job_type"].strip()

    if "work_style" in data:
        fields["work_style"] = data["work_style"].strip()

    if "availability" in data:
        fields["availability"] = data["availability"].strip()

    if "learning_goals" in data:
        fields["learning_goals"] = data["learning_goals"].strip()

    if not fields:
        return json_error("No fields to update", 400)

    db = get_db()
    try:
        cur = db.cursor()
        set_clause = ", ".join(f"{k}=%s" for k in fields)
        cur.execute(
            f"UPDATE users SET {set_clause} WHERE id=%s",
            list(fields.values()) + [user_id]
        )
        db.commit()
    finally:
        db.close()

    return jsonify({"ok": True})