# skill_path_tools.py
# YouthSmartJA - Dijkstra-based skill path recommendation

import heapq
import math
import mysql.connector

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Happy321",
    "database": "youthsmart",
    "port": 3306,
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def normalize_skills(skills):
    return sorted(set(s.lower().strip() for s in skills if s and s.strip()))


def cosine_similarity(student_skills, job_skills):
    student_set = set(student_skills)
    job_set = set(job_skills)

    vocab = sorted(student_set | job_set)
    if not vocab:
        return 0.0

    vec1 = [1 if s in student_set else 0 for s in vocab]
    vec2 = [1 if s in job_set else 0 for s in vocab]

    dot = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot / (mag1 * mag2)


# fallback learning cost if not found elsewhere
SKILL_COST = {
    "excel": 1.0,
    "communication": 1.0,
    "customer service": 1.5,
    "sql": 2.0,
    "mysql": 2.0,
    "postgresql": 2.5,
    "tableau": 2.5,
    "power bi": 2.5,
    "python": 3.0,
    "statistics": 3.0,
    "data visualization": 2.5,
    "machine learning": 5.0,
    "deep learning": 6.0,
    "java": 3.0,
    "javascript": 2.5,
    "typescript": 2.5,
    "react": 3.0,
    "node": 3.0,
    "flask": 2.5,
    "django": 3.0,
    "aws": 4.0,
    "docker": 3.5,
    "git": 1.5,
    "graphql": 2.5,
    "rest": 1.5,
}


# controlled vocabulary of real skills
KNOWN_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "node",
    "sql", "mysql", "postgresql", "docker", "aws", "flask", "django",
    "git", "rest", "graphql", "excel", "communication", "customer service",
    "tableau", "power bi", "statistics", "data visualization",
    "machine learning", "deep learning"
}


def compute_edge_weight(skill, improvement):
    if improvement <= 0:
        return None

    difficulty_cost = SKILL_COST.get(skill, 2.0)
    benefit_term = 1 / (improvement + 1e-6)

    return benefit_term + difficulty_cost


def extract_resume_skills_from_keywords(keywords_csv):
    """
    Convert stored resume keywords into a cleaner skill list by
    keeping only items that exist in the known skill vocabulary.
    """
    if not keywords_csv:
        return []

    raw = [k.strip().lower() for k in keywords_csv.split(",") if k.strip()]
    filtered = [k for k in raw if k in KNOWN_SKILLS]

    return sorted(set(filtered))


def get_latest_resume_keywords(user_id: int) -> str:
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT COALESCE(keywords, '')
        FROM resumes
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row[0] if row else ""


def get_job_skills(job_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT skill
        FROM job_skills
        WHERE job_id=%s
    """, (job_id,))
    rows = cur.fetchall()
    cur.close()
    db.close()
    return normalize_skills([r[0] for r in rows])


def get_job_summary(job_id: int):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT id, title, company, city, country, apply_link
        FROM jobs
        WHERE id=%s
        LIMIT 1
    """, (job_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row


def dijkstra_skill_path(student_skills, job_skills, target_score=0.85):
    student_skills = normalize_skills(student_skills)
    job_skills = normalize_skills(job_skills)
    required_skill_set = set(job_skills)

    if not job_skills:
        return {
            "start_score": 0,
            "final_score": 0,
            "path": [],
            "missing_skills": []
        }

    start_score = cosine_similarity(student_skills, job_skills)
    missing_skills = [s for s in job_skills if s not in student_skills]

    if start_score >= target_score or not missing_skills:
        return {
            "start_score": round(start_score * 100),
            "final_score": round(start_score * 100),
            "path": [],
            "missing_skills": missing_skills
        }

    start_node = frozenset(student_skills)

    dist = {start_node: 0.0}
    prev = {start_node: None}

    pq = []
    counter = 0
    heapq.heappush(pq, (0.0, counter, start_node))

    visited = set()
    best_goal_node = None

    while pq:
        current_cost, _, current_node = heapq.heappop(pq)

        if current_node in visited:
            continue
        visited.add(current_node)

        current_skills = list(current_node)
        current_score = cosine_similarity(current_skills, job_skills)

        # Stop if student is qualified enough
        if current_score >= target_score:
            best_goal_node = current_node
            break

        # Stop if all required job skills are covered,
        # even if the student has extra skills
        if required_skill_set.issubset(current_node):
            best_goal_node = current_node
            break

        remaining_skills = [s for s in job_skills if s not in current_node]

        for skill in remaining_skills:
            next_node = frozenset(set(current_node) | {skill})
            next_skills = list(next_node)

            score_before = current_score
            score_after = cosine_similarity(next_skills, job_skills)
            improvement = score_after - score_before

            edge_weight = compute_edge_weight(skill, improvement)
            if edge_weight is None:
                continue

            new_cost = current_cost + edge_weight

            if next_node not in dist or new_cost < dist[next_node]:
                dist[next_node] = new_cost
                prev[next_node] = {
                    "previous_node": current_node,
                    "skill_learned": skill,
                    "score_before": score_before,
                    "score_after": score_after,
                    "improvement": improvement,
                    "step_cost": edge_weight,
                    "total_cost": new_cost,
                }
                counter += 1
                heapq.heappush(pq, (new_cost, counter, next_node))

    # Fallback: find the cheapest node that contains all required skills
    if best_goal_node is None:
        candidate_goal_nodes = [
            node for node in dist
            if required_skill_set.issubset(node)
        ]

        if candidate_goal_nodes:
            best_goal_node = min(candidate_goal_nodes, key=lambda n: dist[n])
        else:
            return {
                "start_score": round(start_score * 100),
                "final_score": round(start_score * 100),
                "path": [],
                "missing_skills": missing_skills
            }

    path = []
    node = best_goal_node

    while prev[node] is not None:
        step = prev[node]
        path.append({
            "learn": step["skill_learned"],
            "state": sorted(list(node)),
            "score": round(step["score_after"] * 100),
            "improvement": round(step["improvement"] * 100),
            "step_cost": round(step["step_cost"], 2),
            "total_cost": round(step["total_cost"], 2),
        })
        node = step["previous_node"]

    path.reverse()

    final_score = round(cosine_similarity(list(best_goal_node), job_skills) * 100)

    return {
        "start_score": round(start_score * 100),
        "final_score": final_score,
        "path": path,
        "missing_skills": missing_skills
    }


def recommend_skill_path_for_job(user_id: int, job_id: int, target_score: float = 0.85):
    resume_keywords = get_latest_resume_keywords(user_id)
    student_skills = extract_resume_skills_from_keywords(resume_keywords)
    job_skills = get_job_skills(job_id)
    job = get_job_summary(job_id)

    result = dijkstra_skill_path(
        student_skills=student_skills,
        job_skills=job_skills,
        target_score=target_score
    )

    return {
        "job": job,
        "student_skills": student_skills,
        "job_skills": job_skills,
        **result
    }
