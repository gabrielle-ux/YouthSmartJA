# skill_path_tools.py

import heapq
import logging
from mysql.connector.pooling import MySQLConnectionPool
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from cosine_matcher import (
    clean_text,
    get_latest_resume_text,
    get_job_text_by_id,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "captain",
    "password": "captain123",
    "database": "youthsmart",
    "port": 3308,
    "pool_name": "ysja_pool",
    "pool_size": 5,
}

_pool: MySQLConnectionPool | None = None


def _get_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(**DB_CONFIG)
    return _pool


def get_db():
    return _get_pool().get_connection()


# ---------------------------------------------------------------------------
# Skill aliases
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
    "ai imaging": "ai",
    "artificial intelligence": "ai",
}

# ---------------------------------------------------------------------------
# Hardcoded fallbacks
# ---------------------------------------------------------------------------

_FALLBACK_KNOWN_SKILLS: set[str] = {
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "swift", "kotlin", "r",
    "react", "vue", "angular", "node", "flask", "django", "fastapi", "html", "css",
    "spring", "spring boot", "backend", "frontend", "full stack", "software engineering",
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "database", "database design",
    "excel", "tableau", "power bi", "statistics", "data visualization", "data analysis",
    "machine learning", "deep learning", "nlp", "computer vision", "image processing", "ai",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux", "terraform",
    "rest", "rest api", "graphql", "grpc", "api", "microservices",
    "communication", "customer service", "project management", "leadership", "teamwork",
    "problem solving", "critical thinking", "time management", "public speaking", "attention to detail",
    "accounting", "financial analysis", "microsoft office",
}

_FALLBACK_SKILL_COST: dict[str, float] = {
    "communication": 1.0, "teamwork": 1.0, "time management": 1.0,
    "excel": 1.2, "microsoft office": 1.2,
    "git": 1.5, "html": 1.5, "css": 1.5, "customer service": 1.5,
    "rest": 1.5, "rest api": 1.5, "api": 1.5,
    "public speaking": 1.8,
    "leadership": 2.0, "problem solving": 2.0, "critical thinking": 2.0,
    "attention to detail": 2.0, "project management": 2.0,
    "sql": 2.0, "mysql": 2.0, "linux": 2.0,
    "javascript": 2.5, "typescript": 2.5, "tableau": 2.5, "power bi": 2.5,
    "data visualization": 2.5, "data analysis": 2.5,
    "graphql": 2.5, "flask": 2.5, "vue": 2.5,
    "mongodb": 2.5, "redis": 2.5,
    "backend": 2.5, "frontend": 2.5, "database": 2.5, "database design": 2.5,
    "python": 3.0, "java": 3.0, "go": 3.0, "statistics": 3.0, "postgresql": 3.0,
    "react": 3.0, "angular": 3.0, "node": 3.0, "django": 3.0, "fastapi": 2.8,
    "spring": 3.0, "spring boot": 3.2, "microservices": 3.2,
    "r": 3.0, "elasticsearch": 3.0, "c#": 3.5, "ruby": 3.0, "swift": 3.5,
    "kotlin": 3.5, "docker": 3.5,
    "aws": 4.0, "azure": 4.0, "gcp": 4.0, "terraform": 4.0, "c++": 4.0,
    "financial analysis": 3.5, "accounting": 3.5, "kubernetes": 4.5,
    "ai": 4.5, "machine learning": 5.0, "nlp": 5.0,
    "computer vision": 5.5, "image processing": 5.0, "deep learning": 6.0,
}

# ---------------------------------------------------------------------------
# Skill priority groups
# ---------------------------------------------------------------------------

TECHNICAL_SKILLS: set[str] = {
    "python", "java", "javascript", "typescript",
    "react", "vue", "angular", "node",
    "flask", "django", "fastapi", "spring", "spring boot",
    "api", "rest", "rest api", "graphql",
    "backend", "frontend", "full stack", "software engineering",
    "microservices",
    "sql", "mysql", "postgresql", "mongodb",
    "database", "database design",
    "git", "docker", "kubernetes",
    "aws", "azure", "gcp", "linux",
    "ai", "machine learning", "deep learning",
    "computer vision", "image processing",
    "data analysis", "statistics",
}

SOFT_SKILLS: set[str] = {
    "communication", "teamwork", "leadership",
    "problem solving", "critical thinking",
    "time management", "attention to detail",
    "organization", "adaptability", "professionalism",
}

IRRELEVANT_SOFTWARE_SKILLS: set[str] = {
    "retail", "cashier", "food service", "bartending",
    "housekeeping", "front desk", "guest service",
    "tourism", "hospitality",
}

SOFTWARE_CONTEXT_TERMS: set[str] = {
    "developer", "software", "engineer", "backend",
    "frontend", "full stack", "java", "python",
    "api", "database", "spring", "react", "javascript",
    "microservices", "ai", "machine learning",
}

# ---------------------------------------------------------------------------
# Dynamic loading from DB
# ---------------------------------------------------------------------------

def _load_known_skills_from_db() -> set[str]:
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
    db_skills = _load_known_skills_from_db()
    return db_skills | _FALLBACK_KNOWN_SKILLS


def _build_skill_cost() -> dict[str, float]:
    db_costs = _load_skill_costs_from_db()
    return {**_FALLBACK_SKILL_COST, **db_costs}


KNOWN_SKILLS: set[str] = _build_known_skills()
SKILL_COST: dict[str, float] = _build_skill_cost()


def refresh_skill_data() -> None:
    global KNOWN_SKILLS, SKILL_COST
    KNOWN_SKILLS = _build_known_skills()
    SKILL_COST = _build_skill_cost()
    log.info(
        "Skill data refreshed. %d known skills, %d with cost data.",
        len(KNOWN_SKILLS),
        len(SKILL_COST),
    )


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------

PREREQUISITES: dict[str, set[str]] = {
    "machine learning": {"python", "statistics"},
    "deep learning": {"python", "machine learning"},
    "nlp": {"python", "machine learning"},
    "computer vision": {"python", "deep learning"},
    "image processing": {"python"},
    "django": {"python"},
    "flask": {"python"},
    "fastapi": {"python"},
    "spring": {"java"},
    "spring boot": {"java"},
    "react": {"javascript"},
    "angular": {"typescript"},
    "node": {"javascript"},
    "kubernetes": {"docker"},
    "terraform": {"aws"},
    "graphql": {"rest"},
    "postgresql": {"sql"},
    "mysql": {"sql"},
    "mongodb": {"sql"},
}

BEAM_WIDTH = 8
SKILL_LEARN_REPEAT = 4

# Minimum cosine improvement required before a skill is accepted.
# This prevents tiny improvements like 0.0002 from entering the path.
MIN_IMPROVEMENT_THRESHOLD = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalise_skill(raw: str) -> str:
    cleaned = raw.strip().lower()
    return SKILL_ALIASES.get(cleaned, cleaned)


def normalize_skills(skills: list[str]) -> list[str]:
    return sorted(set(normalise_skill(s) for s in skills if s and s.strip()))


def prerequisites_met(skill: str, current_skills: frozenset[str]) -> bool:
    required = PREREQUISITES.get(skill, set())
    return required.issubset(current_skills)


def is_software_context(job_text: str) -> bool:
    job_clean = clean_text(job_text)
    return any(term in job_clean for term in SOFTWARE_CONTEXT_TERMS)


def filter_candidate_skills_for_context(candidate_skills: list[str], job_text: str) -> list[str]:
    """
    Removes clearly irrelevant skills for software/technical jobs.
    Example: retail should not be recommended for Java backend roles.
    """
    if not is_software_context(job_text):
        return candidate_skills

    return [
        skill for skill in candidate_skills
        if skill not in IRRELEVANT_SOFTWARE_SKILLS
    ]


def get_skill_priority(skill: str, job_text: str = "") -> float:
    """
    Lower multiplier = preferred by Dijkstra.
    Higher multiplier = less preferred.
    """
    skill = normalise_skill(skill)

    if is_software_context(job_text) and skill in IRRELEVANT_SOFTWARE_SKILLS:
        return 10.0

    if skill in TECHNICAL_SKILLS:
        return 0.65

    if skill in SOFT_SKILLS:
        return 5.0

    return 1.0


def compute_edge_weight(skill: str, improvement: float, job_text: str = "") -> float | None:
    """
    Lower cost = preferred by Dijkstra.

    Combines:
    - base learning difficulty
    - cosine improvement
    - skill priority/type
    """
    if improvement < MIN_IMPROVEMENT_THRESHOLD:
        return None

    difficulty = SKILL_COST.get(skill, 2.5)
    priority = get_skill_priority(skill, job_text)

    return (difficulty * priority) / (improvement + 1e-6)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

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

def skills_already_in_resume(resume_text: str, candidate_skills: list[str]) -> set[str]:
    if not resume_text or not candidate_skills:
        return set()

    resume_tokens = set(clean_text(resume_text).split())

    already = set()
    for skill in candidate_skills:
        skill_tokens = clean_text(skill).split()
        if skill_tokens and all(t in resume_tokens for t in skill_tokens):
            already.add(skill)

    return already


class _PathScorer:
    def __init__(self, resume_text: str, job_text: str, candidate_skills: list[str]):
        self.resume_clean = clean_text(resume_text)
        self.job_clean = clean_text(job_text)
        self.skills = list(candidate_skills)

        superset_doc = (self.resume_clean + " " + " ".join(self.skills)).strip()
        corpus = [superset_doc, self.job_clean]

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=3000,
        )

        self.vectorizer.fit(corpus)
        self.job_vec = self.vectorizer.transform([self.job_clean])

    def score(self, skillset) -> float:
        if not self.resume_clean or not self.job_clean:
            return 0.0

        if skillset:
            added = " ".join(
                s for s in sorted(skillset)
                for _ in range(SKILL_LEARN_REPEAT)
            )
            doc = (self.resume_clean + " " + added).strip()
        else:
            doc = self.resume_clean

        vec = self.vectorizer.transform([doc])
        return float(cosine_similarity(vec, self.job_vec)[0][0])


def dijkstra_skill_path(
    resume_text: str,
    job_text: str,
    candidate_skills: list[str],
    target_score: float = 0.30,
    beam_width: int = BEAM_WIDTH,
) -> dict:
    resume_text = resume_text or ""
    job_text = job_text or ""

    candidate_skills = normalize_skills(candidate_skills)
    candidate_skills = filter_candidate_skills_for_context(candidate_skills, job_text)

    if not job_text.strip():
        return {
            "start_score": 0,
            "final_score": 0,
            "path": [],
            "missing_skills": [],
            "already_have": [],
            "reached_target": False,
        }

    already_have = skills_already_in_resume(resume_text, candidate_skills)
    skills_to_search = [s for s in candidate_skills if s not in already_have]

    scorer = _PathScorer(resume_text, job_text, skills_to_search)

    total_skills = len(candidate_skills)

    def skill_overlap_score(current_skillset: frozenset) -> float:
        if total_skills == 0:
            return 0.0
        have = len(already_have) + len(current_skillset)
        return have / total_skills

    start_score = skill_overlap_score(frozenset())

    if start_score >= target_score or not skills_to_search:
        return {
            "start_score": round(start_score * 100),
            "final_score": round(start_score * 100),
            "path": [],
            "missing_skills": skills_to_search,
            "already_have": sorted(already_have),
            "reached_target": start_score >= target_score,
        }

    start_node = frozenset()
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
        current_score = skill_overlap_score(current_node)

        if current_score >= target_score:
            best_goal_node = current_node
            break

        remaining = [s for s in skills_to_search if s not in current_node]

        candidates_scored = []
        for skill in remaining:
            if not prerequisites_met(skill, current_node):
                continue

            next_score = skill_overlap_score(current_node | {skill})
            improvement = next_score - current_score

            if improvement >= MIN_IMPROVEMENT_THRESHOLD:
                priority = get_skill_priority(skill, job_text)
                candidates_scored.append((skill, improvement, next_score, priority))

        candidates_scored.sort(
            key=lambda x: (
                compute_edge_weight(x[0], x[1], job_text),
                -x[1],
            )
        )

        candidates = candidates_scored[:beam_width]

        for skill, improvement, score_after, _priority in candidates:
            next_node = frozenset(set(current_node) | {skill})

            edge_weight = compute_edge_weight(skill, improvement, job_text)
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

    if best_goal_node is None and dist:
        best_goal_node = max(
            dist.keys(),
            key=lambda n: (skill_overlap_score(n), -dist[n]),
        )
        log.warning("Target score not reached. Returning best partial path.")

    if best_goal_node is None:
        return {
            "start_score": round(start_score * 100),
            "final_score": round(start_score * 100),
            "path": [],
            "missing_skills": skills_to_search,
            "already_have": sorted(already_have),
            "reached_target": False,
        }

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

    final_score = round(skill_overlap_score(best_goal_node) * 100)
    learned_skills = set(best_goal_node)
    missing_skills = [s for s in skills_to_search if s not in learned_skills]

    return {
        "start_score": round(start_score * 100),
        "final_score": final_score,
        "path": path,
        "missing_skills": missing_skills,
        "already_have": sorted(already_have),
        "reached_target": final_score >= round(target_score * 100),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def recommend_skill_path_for_job(
    user_id: int,
    job_id: int,
    target_score: float = 1.0,
) -> dict:
    resume_text = get_latest_resume_text(user_id)
    job_text = get_job_text_by_id(job_id)
    job_skills = get_job_skills(job_id)
    job = get_job_summary(job_id)

    result = dijkstra_skill_path(
        resume_text=resume_text,
        job_text=job_text,
        candidate_skills=job_skills,
        target_score=target_score,
    )

    return {
        "job": job,
        "candidate_skills": filter_candidate_skills_for_context(job_skills, job_text),
        **result,
    }


# ---------------------------------------------------------------------------
# Test run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    user_id = 1
    job_id = 1

    result = recommend_skill_path_for_job(
        user_id=user_id,
        job_id=job_id,
        target_score=0.30,
    )
    print(result)
