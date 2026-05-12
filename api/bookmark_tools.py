import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()



DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "youthsmart"),
    "port": int(os.getenv("DB_PORT", 3306)),
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def save_bookmark(user_id, job_id, match_score, pref_score, final_score):
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute(
            """
            INSERT INTO bookmarks (user_id, job_id, match_score, pref_score, final_score)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                match_score=VALUES(match_score),
                pref_score=VALUES(pref_score),
                final_score=VALUES(final_score),
                saved_at=CURRENT_TIMESTAMP
            """,
            (user_id, job_id, match_score, pref_score, final_score)
        )
        db.commit()
    finally:
        cur.close()
        db.close()


def get_user_bookmarks(user_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT 
                b.id,
                b.job_id,
                b.match_score,
                b.pref_score,
                b.final_score,
                b.saved_at,
                j.title,
                j.company,
                j.city,
                j.country,
                j.is_remote,
                j.apply_link
            FROM bookmarks b
            JOIN jobs j ON b.job_id = j.id
            WHERE b.user_id = %s
            ORDER BY b.saved_at DESC
            """,
            (user_id,)
        )
        return cur.fetchall()
    finally:
        cur.close()
        db.close()


def delete_bookmark(user_id, job_id):
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute(
            """
            DELETE FROM bookmarks
            WHERE user_id=%s AND job_id=%s
            """,
            (user_id, job_id)
        )
        db.commit()
        return cur.rowcount
    finally:
        cur.close()
        db.close()