# skill_path_tools.py

import os
import heapq
import logging
import math

from dotenv import load_dotenv
from mysql.connector.pooling import MySQLConnectionPool
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from cosine_matcher import (
    clean_text,
    get_latest_resume_text,
    get_job_text_by_id,
)

load_dotenv()

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "youthsmart"),
    "port": int(os.getenv("DB_PORT", 3306)),
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
    "ci/cd": "ci cd",
    "cicd": "ci cd",
    "continuous integration": "ci cd",
    "continuous deployment": "ci cd",
    "english language": "english",
    "ms word": "word",
}

# ---------------------------------------------------------------------------
# Skill context expansion
# Richer context per skill so TF-IDF gives a stronger signal
# when a skill is added to the simulated resume.
# ---------------------------------------------------------------------------

SKILL_CONTEXT: dict[str, str] = {
    # Office / admin
    "excel":              "excel spreadsheet data analysis microsoft office formulas pivot tables",
    "word":               "word document microsoft office writing reports formatting letters",
    "microsoft office":   "microsoft office excel word powerpoint outlook productivity",
    "administration":     "administration office management coordination operations support clerical",
    "organization":       "organization planning coordination management workflow scheduling",
    "database":           "database sql data management queries records storage retrieval",
    "accounting":         "accounting finance bookkeeping ledger payroll invoicing",
    "financial analysis": "financial analysis finance reporting budgeting forecasting",
    "customer service":   "customer service support communication client relations helpdesk",
    "project management": "project management planning coordination delivery agile scrum",
    "public speaking":    "public speaking presentation communication leadership training",
    "communication":      "communication writing presentation teamwork collaboration interpersonal",
    "leadership":         "leadership management team coordination decision making strategy",
    "teamwork":           "teamwork collaboration group work coordination support",
    "problem solving":    "problem solving analytical thinking troubleshooting critical solutions",
    "critical thinking":  "critical thinking analysis evaluation reasoning problem solving",
    "time management":    "time management scheduling prioritization productivity efficiency",
    "attention to detail": "attention to detail accuracy quality review verification",
    # Tech
    "python":             "python programming scripting automation development data backend",
    "java":               "java programming backend spring enterprise development jvm",
    "javascript":         "javascript frontend web development node react programming browser",
    "typescript":         "typescript javascript frontend development static typing angular",
    "react":              "react javascript frontend ui component web development spa",
    "vue":                "vue javascript frontend ui component web development spa",
    "angular":            "angular typescript frontend ui component web development spa",
    "node":               "node javascript backend server api development runtime express",
    "sql":                "sql database queries data management relational records joins",
    "mysql":              "mysql sql database relational queries data management backend",
    "postgresql":         "postgresql sql database relational queries data management backend",
    "mongodb":            "mongodb nosql database document storage queries backend",
    "docker":             "docker containerization deployment devops infrastructure backend",
    "kubernetes":         "kubernetes container orchestration deployment devops infrastructure backend",
    "aws":                "aws cloud computing infrastructure deployment services backend",
    "azure":              "azure cloud computing microsoft infrastructure deployment backend",
    "gcp":                "gcp google cloud computing infrastructure deployment backend",
    "git":                "git version control source code management collaboration backend developer repository branching",
    "linux":              "linux operating system server administration command line backend",
    "machine learning":   "machine learning ai data science models training algorithms python",
    "deep learning":      "deep learning neural networks ai computer vision nlp python",
    "ai":                 "artificial intelligence machine learning data models automation python",
    "nlp":                "nlp natural language processing text analysis machine learning python",
    "data analysis":      "data analysis statistics visualization insights reporting excel",
    "statistics":         "statistics data analysis probability modelling research python r",
    "rest":               "rest api web services http integration backend endpoints json",
    "rest api":           "rest api web services http integration backend endpoints json",
    "api":                "api rest web services http integration backend endpoints developer",
    "graphql":            "graphql api query language backend integration developer",
    "flask":              "flask python web framework backend api development rest",
    "django":             "django python web framework backend development rest",
    "fastapi":            "fastapi python web framework backend api development rest",
    "spring":             "spring java framework backend enterprise development rest api",
    "spring boot":        "spring boot java framework backend microservices development rest",
    "backend":            "backend server api development database rest java python node developer",
    "frontend":           "frontend ui ux web development javascript react vue html css developer",
    "full stack":         "full stack frontend backend developer javascript python api database web",
    "microservices":      "microservices architecture backend distributed systems api docker kubernetes",
    "terraform":          "terraform infrastructure as code devops cloud deployment aws",
    "redis":              "redis cache in-memory database performance backend api",
    "elasticsearch":      "elasticsearch search engine data indexing backend api",
    "tableau":            "tableau data visualization business intelligence reporting dashboard",
    "power bi":           "power bi data visualization business intelligence reporting dashboard",
    "c++":                "c++ systems programming performance backend development low level",
    "c#":                 "c# dotnet microsoft backend development enterprise api",
    "swift":              "swift ios mobile apple development programming xcode",
    "kotlin":             "kotlin android mobile development programming jvm backend",
    "go":                 "go golang backend systems programming performance api",
    "r":                  "r statistics data analysis programming research modelling",
    "computer vision":    "computer vision image processing deep learning ai detection python",
    "image processing":   "image processing computer vision python ai analysis detection",
    "software engineering": "software engineering development backend frontend java python api",
    "database design":    "database design sql schema modelling relational queries backend",
    "data visualization": "data visualization charts graphs reporting tableau power bi excel",
    "grpc":               "grpc api protocol backend microservices distributed systems",
}


def _expand_skill(skill: str) -> str:
    """Return a rich context string for a skill to boost TF-IDF signal."""
    return SKILL_CONTEXT.get(skill, f"{skill} project experience work professional developer")


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
    # -----------------------------------------------------------------
    # Tier 1 — Beginner (1–2 weeks to pick up basics)
    # -----------------------------------------------------------------
    "communication": 1.0,
    "teamwork": 1.0,
    "time management": 1.0,
    "attention to detail": 1.0,
    "microsoft office": 1.2,
    "excel": 1.5,          # basic use is easy; advanced takes longer
    "html": 1.5,
    "css": 1.5,
    "git": 1.8,            # essential but learnable in days
    "customer service": 1.5,
    "public speaking": 1.8,

    # -----------------------------------------------------------------
    # Tier 2 — Intermediate (1–4 weeks, needs practice)
    # -----------------------------------------------------------------
    "rest": 2.0,
    "rest api": 2.0,
    "api": 2.0,
    "sql": 2.2,
    "linux": 2.5,
    "problem solving": 2.0,
    "critical thinking": 2.0,
    "leadership": 2.0,
    "project management": 2.5,
    "database": 2.5,
    "database design": 2.8,
    "data analysis": 2.5,
    "data visualization": 2.5,
    "tableau": 2.5,
    "power bi": 2.5,

    # -----------------------------------------------------------------
    # Tier 3 — Solid effort (1–3 months)
    # -----------------------------------------------------------------
    "javascript": 3.0,
    "typescript": 3.5,     # harder than JS — needs JS first
    "python": 3.0,
    "mysql": 2.8,
    "postgresql": 3.0,
    "mongodb": 3.0,
    "redis": 3.2,
    "backend": 3.0,
    "frontend": 3.0,
    "flask": 3.2,          # needs Python first
    "fastapi": 3.3,
    "node": 3.5,           # needs JS first
    "vue": 3.5,            # needs JS first
    "react": 4.0,          # needs JS + ecosystem understanding
    "angular": 4.5,        # needs TypeScript + steep learning curve
    "django": 3.8,         # needs Python + more conventions than Flask
    "java": 4.0,           # verbose, stricter than Python
    "go": 4.0,
    "ruby": 3.5,
    "c#": 4.0,
    "docker": 3.8,
    "graphql": 3.5,        # needs REST understanding first
    "elasticsearch": 3.8,
    "statistics": 3.5,
    "accounting": 3.5,
    "financial analysis": 3.8,
    "full stack": 4.0,     # combines frontend + backend
    "microservices": 4.0,
    "software engineering": 3.5,

    # -----------------------------------------------------------------
    # Tier 4 — Advanced (3–6 months, real projects needed)
    # -----------------------------------------------------------------
    "spring": 4.5,         # needs Java + enterprise patterns
    "spring boot": 4.8,
    "kotlin": 4.5,
    "swift": 5.0,
    "c++": 5.5,            # memory management, complex syntax
    "r": 4.0,
    "aws": 5.0,            # huge surface area
    "azure": 5.0,
    "gcp": 5.0,
    "terraform": 5.0,      # needs cloud knowledge first
    "kubernetes": 5.5,     # needs Docker + distributed systems understanding
    "grpc": 4.5,

    # -----------------------------------------------------------------
    # Tier 5 — Expert (6+ months, math/research heavy)
    # -----------------------------------------------------------------
    "ai": 6.0,
    "machine learning": 7.0,   # needs stats + python + math
    "nlp": 7.5,                # needs ML + linguistics understanding
    "data analysis": 2.5,      # basic is easy; already in tier 2
    "image processing": 7.0,
    "computer vision": 8.0,    # needs deep learning + math
    "deep learning": 9.0,      # hardest — needs ML + linear algebra + GPU
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
    "ci cd", "devops", "jenkins", "github actions",
    "terraform", "redis", "grpc",
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
# Blended score weights
# 70% cosine similarity + 30% skill coverage
# Skill coverage = what % of the job's required skills this skillset covers.
# This gives meaningful per-step jumps even when TF-IDF signal is weak.
# ---------------------------------------------------------------------------
COSINE_WEIGHT = 0.70
COVERAGE_WEIGHT = 0.30

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

# ---------------------------------------------------------------------------
# Speed / quality controls
# ---------------------------------------------------------------------------
BEAM_WIDTH = 4                     # paths explored per step
SKILL_LEARN_REPEAT = 15            # default fallback repeat count
MIN_IMPROVEMENT_THRESHOLD = 0.005  # at least +0.5% before a skill becomes a roadmap step
MAX_SKILLS_TO_TEST = 15            # max missing skills to run Dijkstra over
MAX_TARGET_GAIN = 0.30             # roadmap target is at most +30% above current score

# Skills that should not appear as learning-roadmap steps.
# They may still be shown elsewhere, but Guidance Mode should focus on skills
# that produce clear career/technical growth.
GENERIC_ROADMAP_EXCLUDE: set[str] = {
    "english", "writing", "word", "microsoft office",
    "communication", "teamwork", "attention to detail",
    "problem solving", "leadership", "time management", "critical thinking",
    "adaptability", "professionalism", "organization", "public speaking",
    "presentation", "research",
}

SOFTWARE_ROADMAP_EXCLUDE: set[str] = {
    "excel", "administration", "customer service", "accounting",
    "financial analysis", "office", "clerical",
}

# ---------------------------------------------------------------------------
# Per-skill repeat counts — controls how much each skill boosts the score.
# Higher = bigger improvement signal for that skill = more differentiated values.
# Core tech skills get high values, soft/easy skills get low values.
# ---------------------------------------------------------------------------
SKILL_IMPORTANCE: dict[str, int] = {
    # --- Core languages (biggest signal) ---
    "python":           30,
    "javascript":       30,
    "java":             28,
    "typescript":       28,
    "c++":              25,
    "c#":               25,
    "go":               25,
    "kotlin":           22,
    "swift":            22,
    "ruby":             20,
    "r":                18,

    # --- Frontend frameworks ---
    "react":            28,
    "angular":          26,
    "vue":              24,
    "node":             26,
    "html":             12,
    "css":              12,

    # --- Backend frameworks ---
    "flask":            26,
    "django":           26,
    "fastapi":          24,
    "spring":           26,
    "spring boot":      26,

    # --- APIs ---
    "rest api":         22,
    "rest":             20,
    "api":              18,
    "graphql":          22,
    "grpc":             20,

    # --- Databases ---
    "sql":              22,
    "mysql":            20,
    "postgresql":       20,
    "mongodb":          20,
    "redis":            18,
    "elasticsearch":    18,
    "database":         16,
    "database design":  18,

    # --- DevOps / Cloud ---
    "aws":              26,
    "azure":            26,
    "gcp":              24,
    "docker":           24,
    "kubernetes":       26,
    "terraform":        22,
    "linux":            18,
    "git":              12,
    "ci cd":            20,
    "devops":           22,
    "jenkins":          18,
    "github actions":   16,
    "ansible":          18,

    # --- AI / Data ---
    "machine learning": 28,
    "deep learning":    28,
    "ai":               24,
    "nlp":              26,
    "computer vision":  26,
    "image processing": 22,
    "data analysis":    20,
    "statistics":       20,
    "pandas":           18,
    "numpy":            16,
    "scikit learn":     22,
    "tensorflow":       26,
    "pytorch":          26,
    "spark":            22,
    "airflow":          20,
    "bigquery":         18,
    "snowflake":        18,
    "dbt":              16,
    "etl":              18,
    "data pipeline":    20,
    "data engineering": 22,
    "llm":              24,
    "generative ai":    22,
    "prompt engineering": 16,

    # --- Security / IAM ---
    "cybersecurity":    24,
    "iam":              22,
    "active directory": 18,
    "okta":             16,
    "sso":              14,
    "saml":             16,
    "oauth":            18,
    "zero trust":       20,
    "siem":             20,
    "penetration testing": 24,

    # --- General / soft (low signal — shouldn't dominate roadmap) ---
    "excel":            10,
    "tableau":          12,
    "power bi":         12,
    "data visualization": 12,
    "microsoft office": 8,
    "communication":    6,
    "teamwork":         6,
    "leadership":       8,
    "problem solving":  8,
    "project management": 10,
    "customer service": 6,
    "accounting":       10,
    "financial analysis": 12,
}


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
    if not is_software_context(job_text):
        return candidate_skills
    return [
        skill for skill in candidate_skills
        if skill not in IRRELEVANT_SOFTWARE_SKILLS
    ]


def should_consider_roadmap_skill(skill: str, job_text: str) -> bool:
    """Return True only for skills worth showing as roadmap steps."""
    skill = normalise_skill(skill)

    if skill in GENERIC_ROADMAP_EXCLUDE:
        return False

    if is_software_context(job_text) and skill in SOFTWARE_ROADMAP_EXCLUDE:
        return False

    if is_software_context(job_text) and skill in SOFT_SKILLS:
        return False

    if skill in IRRELEVANT_SOFTWARE_SKILLS:
        return False

    return True


def get_skill_priority(skill: str, job_text: str = "") -> float:
    skill = normalise_skill(skill)

    if is_software_context(job_text) and skill in IRRELEVANT_SOFTWARE_SKILLS:
        return 10.0

    if skill in TECHNICAL_SKILLS:
        return 0.65

    if skill in SOFT_SKILLS:
        return 5.0

    return 1.0


def compute_edge_weight(skill: str, improvement: float, job_text: str = "") -> float | None:
    if improvement <= 0 or improvement < MIN_IMPROVEMENT_THRESHOLD:
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
    def __init__(
        self,
        resume_text: str,
        job_text: str,
        candidate_skills: list[str],
        all_job_skills: list[str],
        already_have: set[str],
    ):
        self.resume_clean = clean_text(resume_text)
        self.job_clean = clean_text(job_text)
        self.skills = list(candidate_skills)

        # Total job skills used for coverage calculation.
        # Includes skills the user already has so coverage reflects the full picture.
        self.total_job_skills = len(all_job_skills) if all_job_skills else 1
        self.already_have_count = len(already_have)

        # Build superset doc using expanded skill context so the vectorizer
        # vocabulary includes all relevant terms from the start.
        expanded_skills = " ".join(_expand_skill(s) for s in candidate_skills)
        superset_doc = (self.resume_clean + " " + expanded_skills).strip()
        corpus = [superset_doc, self.job_clean]

        # Bigrams + higher max_features for richer matching signal.
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

        # --- Cosine similarity component ---
        if skillset:
            added = " ".join(
                _expand_skill(s)
                for s in sorted(skillset)
                for _ in range(SKILL_IMPORTANCE.get(s, SKILL_LEARN_REPEAT))
            )
            doc = (self.resume_clean + " " + added).strip()
        else:
            doc = self.resume_clean

        vec = self.vectorizer.transform([doc])
        cosine = float(cosine_similarity(vec, self.job_vec)[0][0])

        # --- Skill coverage component ---
        # (skills already in resume + skills learned so far) / total job skills
        skills_covered = self.already_have_count + len(skillset)
        coverage = min(skills_covered / self.total_job_skills, 1.0)

        # --- Blended score ---
        return (COSINE_WEIGHT * cosine) + (COVERAGE_WEIGHT * coverage)


def dijkstra_skill_path(
    resume_text: str,
    job_text: str,
    candidate_skills: list[str],
    target_score: float = 0.30,
    beam_width: int = BEAM_WIDTH,
) -> dict:
    """
    Build a realistic learning roadmap by simulating each missing skill.

    Scoring is a blend of:
    - 70% cosine similarity between simulated resume and job description
    - 30% skill coverage (how many job skills the user now has)

    This gives meaningful per-step score jumps even when TF-IDF signal is weak.
    """
    resume_text = resume_text or ""
    job_text = job_text or ""

    candidate_skills = normalize_skills(candidate_skills)
    candidate_skills = filter_candidate_skills_for_context(candidate_skills, job_text)

    if not job_text.strip():
        return {
            "start_score": 0,
            "final_score": 0,
            "target_score": 0,
            "requested_target_score": round(target_score * 100),
            "path": [],
            "missing_skills": [],
            "remaining_missing_skills": [],
            "already_have": [],
            "reached_target": False,
        }

    already_have = skills_already_in_resume(resume_text, candidate_skills)

    skills_to_search = [
        s for s in candidate_skills
        if s not in already_have and should_consider_roadmap_skill(s, job_text)
    ]

    skills_to_search = sorted(
        skills_to_search,
        key=lambda s: (get_skill_priority(s, job_text), SKILL_COST.get(s, 2.5), s),
    )[:MAX_SKILLS_TO_TEST]

    scorer = _PathScorer(
        resume_text=resume_text,
        job_text=job_text,
        candidate_skills=skills_to_search,
        all_job_skills=candidate_skills,
        already_have=already_have,
    )

    start_node = frozenset()
    start_score = scorer.score(start_node)

    requested_target_score = max(0.0, min(float(target_score), 1.0))
    # Do not chase an unrealistic 85%/100% target when the current match is low.
    # Example: if start is 18% and requested target is 100%, use 48%.
    practical_target_score = max(0.0, min(requested_target_score, start_score + MAX_TARGET_GAIN, 1.0))

    if start_score >= practical_target_score or not skills_to_search:
        return {
            "start_score": round(start_score * 100),
            "final_score": round(start_score * 100),
            "target_score": round(practical_target_score * 100),
            "requested_target_score": round(requested_target_score * 100),
            "path": [],
            "missing_skills": skills_to_search,
            "remaining_missing_skills": skills_to_search,
            "already_have": sorted(already_have),
            "reached_target": start_score >= practical_target_score,
        }

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
        current_score = scorer.score(current_node)

        if current_score >= practical_target_score:
            best_goal_node = current_node
            break

        remaining = [s for s in skills_to_search if s not in current_node]
        candidates_scored = []

        for skill in remaining:
            current_known_skills = frozenset(set(current_node) | already_have)
            if not prerequisites_met(skill, current_known_skills):
                continue

            next_node = frozenset(set(current_node) | {skill})
            next_score = scorer.score(next_node)
            improvement = next_score - current_score

            edge_weight = compute_edge_weight(skill, improvement, job_text)

            if edge_weight is not None:
                candidates_scored.append((skill, improvement, next_score, edge_weight))

        candidates_scored.sort(key=lambda x: (x[3], -x[1], x[0]))
        candidates = candidates_scored[:beam_width]

        for skill, improvement, score_after, edge_weight in candidates:
            next_node = frozenset(set(current_node) | {skill})
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
            key=lambda n: (scorer.score(n), -dist[n]),
        )
        log.warning("Target score not reached. Returning best partial path.")

    if best_goal_node is None:
        return {
            "start_score": round(start_score * 100),
            "final_score": round(start_score * 100),
            "target_score": round(practical_target_score * 100),
            "requested_target_score": round(requested_target_score * 100),
            "path": [],
            "missing_skills": skills_to_search,
            "remaining_missing_skills": skills_to_search,
            "already_have": sorted(already_have),
            "reached_target": False,
        }

    path = []
    node = best_goal_node

    while prev.get(node) is not None:
        step = prev[node]

        displayed_improvement = max(1, math.ceil(step["improvement"] * 100))

        path.append({
            "learn": step["skill_learned"],
            "score": round(step["score_after"] * 100),
            "improvement": displayed_improvement,
            "raw_improvement": round(step["improvement"] * 100, 2),
            "step_cost": round(step["step_cost"], 2),
            "total_cost": round(step["total_cost"], 2),
        })

        node = step["previous_node"]

    path.reverse()

    final_score_float = scorer.score(best_goal_node)
    final_score = round(final_score_float * 100)
    learned_skills = set(best_goal_node)

    remaining_missing_skills = [
        s for s in skills_to_search
        if s not in learned_skills
    ]

    return {
        "start_score": round(start_score * 100),
        "final_score": final_score,
        "target_score": round(practical_target_score * 100),
        "requested_target_score": round(requested_target_score * 100),
        "path": path,
        "missing_skills": skills_to_search,
        "remaining_missing_skills": remaining_missing_skills,
        "already_have": sorted(already_have),
        "reached_target": final_score_float >= practical_target_score,
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