"""
YouthSmartJA - Dijkstra-based skill path recommendation (improved)
"""



import heapq
import logging
import math
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Happy321",
    "database": "youthsmart",
    "port": 3306,
    "pool_name": "ysja_pool",
    "pool_size": 5,
}

_pool: MySQLConnectionPool | None = None


def _get_pool() -> MySQLConnectionPool:
    """Lazy-initialise a single module-level connection pool."""
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(**DB_CONFIG)
    return _pool


def get_db():
    return _get_pool().get_connection()


# ---------------------------------------------------------------------------
# Alias normalisation
# Maps alternative spellings to the canonical form before any DB or dict lookup.
# ---------------------------------------------------------------------------

SKILL_ALIASES: dict[str, str] = {
    "nodejs": "node",
    "node.js": "node",
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "dl": "deep learning",
    "js": "javascript",
    "ts": "typescript",
    "powerbi": "power bi",
    "ms office": "microsoft office",
    "office": "microsoft office",
}

# ---------------------------------------------------------------------------
# Hardcoded fallbacks
# These are only used for skills that aren't found in the DB.
# The DB is always the primary source — these fill the gaps.
# ---------------------------------------------------------------------------

_FALLBACK_KNOWN_SKILLS: set[str] = {
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "swift", "kotlin", "r",
    "react", "vue", "angular", "node", "flask", "django", "fastapi", "html", "css",
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "excel", "tableau", "power bi", "statistics", "data visualization",
    "machine learning", "deep learning", "nlp", "computer vision",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux", "terraform",
    "rest", "graphql", "grpc",
    "communication", "customer service", "project management", "leadership", "teamwork",
    "problem solving", "critical thinking", "time management", "public speaking",
    "accounting", "financial analysis", "microsoft office",
}

_FALLBACK_SKILL_COST: dict[str, float] = {
    "communication": 1.0, "teamwork": 1.0, "time management": 1.0,
    "excel": 1.2, "microsoft office": 1.2,
    "git": 1.5, "html": 1.5, "css": 1.5, "customer service": 1.5, "rest": 1.5,
    "public speaking": 1.8,
    "leadership": 2.0, "problem solving": 2.0, "critical thinking": 2.0,
    "project management": 2.0, "sql": 2.0, "mysql": 2.0, "linux": 2.0,
    "javascript": 2.5, "typescript": 2.5, "tableau": 2.5, "power bi": 2.5,
    "data visualization": 2.5, "graphql": 2.5, "flask": 2.5, "vue": 2.5,
    "mongodb": 2.5, "redis": 2.5,
    "python": 3.0, "java": 3.0, "go": 3.0, "statistics": 3.0, "postgresql": 3.0,
    "react": 3.0, "angular": 3.0, "node": 3.0, "django": 3.0, "fastapi": 2.8,
    "r": 3.0, "elasticsearch": 3.0, "c#": 3.5, "ruby": 3.0, "swift": 3.5,
    "kotlin": 3.5, "docker": 3.5,
    "aws": 4.0, "azure": 4.0, "gcp": 4.0, "terraform": 4.0, "c++": 4.0,
    "financial analysis": 3.5, "accounting": 3.5, "kubernetes": 4.5,
    "machine learning": 5.0, "nlp": 5.0, "computer vision": 5.5, "deep learning": 6.0,
}

# ---------------------------------------------------------------------------
# Dynamic loading from DB
# ---------------------------------------------------------------------------

def _load_known_skills_from_db() -> set[str]:
    """
    Pull every distinct skill from the job_skills table.
    Returns an empty set (triggering fallback) if the table is empty or missing.
    """
    try:
        db = get_db()
        try:
            cur = db.cursor()
            cur.execute("SELECT DISTINCT LOWER(TRIM(skill)) FROM job_skills WHERE skill IS NOT NULL")
            skills = {row[0] for row in cur.fetchall() if row[0]}
            if skills:
                log.info("Loaded %d known skills from job_skills table.", len(skills))
            return skills
        finally:
            db.close()
    except Exception as exc:
        log.warning("Could not load skills from DB (%s). Using hardcoded fallback.", exc)
        return set()


def _load_skill_costs_from_db() -> dict[str, float]:
    """
    Build a skill → difficulty cost mapping from the courses table.

    Uses AVG(duration_hours) as the difficulty proxy. Skills with no matching
    course fall back to the hardcoded _FALLBACK_SKILL_COST value (or 2.5).

    Requires a `courses` table with at least:
        skill          VARCHAR   -- the skill the course teaches
        duration_hours FLOAT     -- how long the course takes to complete
    """
    try:
        db = get_db()
        try:
            cur = db.cursor()
            cur.execute("""
                SELECT LOWER(TRIM(skill)), AVG(duration_hours)
                FROM courses
                WHERE skill IS NOT NULL AND duration_hours IS NOT NULL
                GROUP BY LOWER(TRIM(skill))
            """)
            costs = {}
            for skill, avg_hours in cur.fetchall():
                if skill and avg_hours is not None:
                    costs[skill] = round(float(avg_hours), 2)
            if costs:
                log.info("Loaded difficulty costs for %d skills from courses table.", len(costs))
            return costs
        finally:
            db.close()
    except Exception as exc:
        log.warning("Could not load skill costs from DB (%s). Using hardcoded fallback.", exc)
        return {}


def _build_known_skills() -> set[str]:
    """Merge DB skills with hardcoded fallback — DB wins on overlap."""
    db_skills = _load_known_skills_from_db()
    # Always include the fallback set so nothing is lost if the DB is new/empty
    return db_skills | _FALLBACK_KNOWN_SKILLS


def _build_skill_cost() -> dict[str, float]:
    """Merge DB costs with hardcoded fallback — DB wins on overlap."""
    db_costs = _load_skill_costs_from_db()
    # Start with fallback, then overwrite with real DB values
    merged = {**_FALLBACK_SKILL_COST, **db_costs}
    return merged


# Module-level dicts built once at import time.
# Call refresh_skill_data() to reload without restarting the server.
KNOWN_SKILLS: set[str] = _build_known_skills()
SKILL_COST: dict[str, float] = _build_skill_cost()


def refresh_skill_data() -> None:
    """
    Reload KNOWN_SKILLS and SKILL_COST from the DB.
    Call this after bulk-importing new jobs or courses so the algorithm
    picks up the new data without needing a server restart.
    """
    global KNOWN_SKILLS, SKILL_COST
    KNOWN_SKILLS = _build_known_skills()
    SKILL_COST = _build_skill_cost()
    log.info("Skill data refreshed. %d known skills, %d with cost data.",
             len(KNOWN_SKILLS), len(SKILL_COST))

# ---------------------------------------------------------------------------
# Skill prerequisites
# A skill should not be recommended before its dependencies are met.
# Keys are skills; values are sets of skills that must be learned first.
# ---------------------------------------------------------------------------

PREREQUISITES: dict[str, set[str]] = {
    "machine learning":  {"python", "statistics"},
    "deep learning":     {"python", "machine learning"},
    "nlp":               {"python", "machine learning"},
    "computer vision":   {"python", "deep learning"},
    "django":            {"python"},
    "flask":             {"python"},
    "fastapi":           {"python"},
    "react":             {"javascript"},
    "angular":           {"typescript"},
    "node":              {"javascript"},
    "kubernetes":        {"docker"},
    "terraform":         {"aws"},   # most common pairing
    "graphql":           {"rest"},
    "postgresql":        {"sql"},
    "mysql":             {"sql"},
    "mongodb":           {"sql"},   # soft prerequisite — understanding of DB concepts
}

# Number of candidate skills examined at each Dijkstra expansion.
# Keeps worst-case nodes manageable: O(N × K) rather than O(2^N).
BEAM_WIDTH = 8


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalise_skill(raw: str) -> str:
    """Lowercase, strip, and resolve aliases."""
    cleaned = raw.strip().lower()
    return SKILL_ALIASES.get(cleaned, cleaned)


def normalize_skills(skills: list[str]) -> list[str]:
    """Deduplicate and sort a skill list."""
    return sorted(set(normalise_skill(s) for s in skills if s and s.strip()))


def cosine_similarity(student_skills: list[str], job_skills: list[str]) -> float:
    """Binary cosine similarity between two skill lists."""
    student_set = set(student_skills)
    job_set = set(job_skills)
    vocab = student_set | job_set
    if not vocab:
        return 0.0
    dot = len(student_set & job_set)
    mag1 = math.sqrt(len(student_set))
    mag2 = math.sqrt(len(job_set))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def prerequisites_met(skill: str, current_skills: frozenset[str]) -> bool:
    """Return True if all prerequisites for `skill` are already in `current_skills`."""
    required = PREREQUISITES.get(skill, set())
    return required.issubset(current_skills)


def compute_edge_weight(skill: str, improvement: float) -> float | None:
    """
    Compute the cost of acquiring `skill`.

    Improvement: how much the cosine score rises after gaining this skill (0–1).

    Old formula:  1 / improvement + difficulty       (improvement term dominates wildly)
    New formula:  difficulty / (improvement + ε)     (balanced: high difficulty + low gain = expensive)

    Lower weight = Dijkstra will prefer this edge.
    """
    if improvement <= 0:
        return None  # skill provides no score gain — skip it

    difficulty = SKILL_COST.get(skill, 2.5)
    return difficulty / (improvement + 1e-6)


def extract_resume_skills_from_keywords(keywords_csv: str) -> list[str]:
    """
    Convert stored resume keywords into a clean, canonical skill list.

    v1 filtered strictly to KNOWN_SKILLS, silently dropping anything else.
    v2 also resolves aliases before filtering, so "nodejs", "k8s", etc. survive.
    """
    if not keywords_csv:
        return []

    raw = [normalise_skill(k) for k in keywords_csv.split(",") if k.strip()]
    filtered = [k for k in raw if k in KNOWN_SKILLS]
    return sorted(set(filtered))


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_latest_resume_keywords(user_id: int) -> str:
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute(
            "SELECT COALESCE(keywords, '') FROM resumes WHERE user_id=%s ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
        return row[0] if row else ""
    finally:
        db.close()


def get_job_skills(job_id: int) -> list[str]:
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute("SELECT skill FROM job_skills WHERE job_id=%s", (job_id,))
        return normalize_skills([r[0] for r in cur.fetchall()])
    finally:
        db.close()


def get_job_summary(job_id: int) -> dict | None:
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT id, title, company, city, country, apply_link FROM jobs WHERE id=%s LIMIT 1",
            (job_id,),
        )
        return cur.fetchone()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------

def dijkstra_skill_path(
    student_skills: list[str],
    job_skills: list[str],
    target_score: float = 0.85,
    beam_width: int = BEAM_WIDTH,
) -> dict:
    """
    Find the lowest-cost sequence of skills to learn in order to raise the
    student's cosine similarity score against a job description.

    Returns a dict with:
        start_score  – initial match percentage (0–100)
        final_score  – achieved match percentage after following the path
        path         – ordered list of skill-learning steps
        missing_skills – skills in the job not currently held by the student
        reached_target – whether the target score was hit
    """
    student_skills = normalize_skills(student_skills)
    job_skills = normalize_skills(job_skills)
    required_skill_set = set(job_skills)

    if not job_skills:
        return {
            "start_score": 0, "final_score": 0,
            "path": [], "missing_skills": [], "reached_target": True,
        }

    start_score = cosine_similarity(student_skills, job_skills)
    missing_skills = [s for s in job_skills if s not in student_skills]

    if start_score >= target_score or not missing_skills:
        return {
            "start_score": round(start_score * 100),
            "final_score": round(start_score * 100),
            "path": [], "missing_skills": missing_skills, "reached_target": True,
        }

    start_node = frozenset(student_skills)
    dist: dict[frozenset, float] = {start_node: 0.0}
    prev: dict[frozenset, dict | None] = {start_node: None}

    pq: list[tuple[float, int, frozenset]] = []
    counter = 0
    heapq.heappush(pq, (0.0, counter, start_node))

    visited: set[frozenset] = set()
    best_goal_node: frozenset | None = None

    while pq:
        current_cost, _, current_node = heapq.heappop(pq)

        if current_node in visited:
            continue
        visited.add(current_node)

        current_score = cosine_similarity(list(current_node), job_skills)

        if current_score >= target_score or required_skill_set.issubset(current_node):
            best_goal_node = current_node
            break

        remaining = [s for s in job_skills if s not in current_node]

        # --- IMPROVEMENT: prune to top-K candidates by potential improvement ---
        # Score each remaining skill and keep only the most promising ones.
        # This caps expansions at beam_width per node instead of all N remainders.
        candidates_scored = []
        for skill in remaining:
            if not prerequisites_met(skill, current_node):
                continue  # honour prerequisite ordering
            next_skills = list(current_node | {skill})
            improvement = cosine_similarity(next_skills, job_skills) - current_score
            if improvement > 0:
                candidates_scored.append((skill, improvement))

        # Sort descending by improvement, keep top beam_width
        candidates_scored.sort(key=lambda x: x[1], reverse=True)
        candidates = candidates_scored[:beam_width]

        for skill, improvement in candidates:
            next_node = frozenset(current_node | {skill})
            score_after = current_score + improvement

            edge_weight = compute_edge_weight(skill, improvement)
            if edge_weight is None:
                continue

            new_cost = current_cost + edge_weight

            if next_node not in dist or new_cost < dist[next_node]:
                dist[next_node] = new_cost
                prev[next_node] = {
                    "previous_node": current_node,
                    "skill_learned": skill,
                    "score_before": current_score,
                    "score_after": score_after,
                    "improvement": improvement,
                    "step_cost": edge_weight,
                    "total_cost": new_cost,
                }
                counter += 1
                heapq.heappush(pq, (new_cost, counter, next_node))

    # --- IMPROVEMENT: smarter fallback ---
    # If we never hit the target, find the best explored node
    # (most skills covered, lowest cost as tiebreak) instead of giving up.
    if best_goal_node is None:
        candidates_with_full_cover = [
            node for node in dist if required_skill_set.issubset(node)
        ]
        if candidates_with_full_cover:
            best_goal_node = min(candidates_with_full_cover, key=lambda n: dist[n])
        elif dist:
            # Partial fallback: the explored node with the highest cosine score
            best_goal_node = max(
                dist.keys(),
                key=lambda n: (cosine_similarity(list(n), job_skills), -dist[n]),
            )
            log.warning(
                "Target score %.0f%% not reachable with current skill graph. "
                "Returning best partial path.",
                target_score * 100,
            )

    if best_goal_node is None:
        return {
            "start_score": round(start_score * 100),
            "final_score": round(start_score * 100),
            "path": [], "missing_skills": missing_skills, "reached_target": False,
        }

    # Reconstruct path
    path = []
    node = best_goal_node
    while prev.get(node) is not None:
        step = prev[node]
        path.append({
            "learn": step["skill_learned"],
            "score": round(step["score_after"] * 100),
            "improvement": round(step["improvement"] * 100),
            "step_cost": round(step["step_cost"], 2),
            "total_cost": round(step["total_cost"], 2),
        })
        node = step["previous_node"]

    path.reverse()

    final_score = round(cosine_similarity(list(best_goal_node), job_skills) * 100)
    reached = final_score >= round(target_score * 100)

    return {
        "start_score": round(start_score * 100),
        "final_score": final_score,
        "path": path,
        "missing_skills": missing_skills,
        "reached_target": reached,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def recommend_skill_path_for_job(
    user_id: int,
    job_id: int,
    target_score: float = 0.85,
) -> dict:
    """
    Full pipeline: load resume + job skills from DB, run Dijkstra, return result.
    """
    resume_keywords = get_latest_resume_keywords(user_id)
    student_skills = extract_resume_skills_from_keywords(resume_keywords)
    job_skills = get_job_skills(job_id)
    job = get_job_summary(job_id)

    result = dijkstra_skill_path(
        student_skills=student_skills,
        job_skills=job_skills,
        target_score=target_score,
    )

    return {
        "job": job,
        "student_skills": student_skills,
        "job_skills": job_skills,
        **result,
    }
