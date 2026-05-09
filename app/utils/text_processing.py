import re

# Move your ALIASES, KNOWN_SKILLS, and NOISE_SKILLS here as well
KNOWN_SKILLS = {

    # ------------------------------------------------
    # Software / IT
    # ------------------------------------------------
    "python",
    "java",
    "javascript",
    "typescript",
    "html",
    "css",

    "react",
    "vue",
    "angular",
    "node",
    "flask",
    "django",
    "spring",
    "spring boot",

    "api",
    "rest",
    "rest api",
    "graphql",

    "backend",
    "frontend",
    "full stack",
    "software engineering",
    "microservices",

    "database",
    "database design",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",

    "git",
    "github",

    "docker",
    "kubernetes",

    "aws",
    "azure",
    "gcp",
    "linux",

    # ------------------------------------------------
    # AI / Data Science
    # ------------------------------------------------
    "machine learning",
    "deep learning",
    "computer vision",
    "image processing",
    "artificial intelligence",
    "ai",

    "data analysis",
    "data entry",
    "statistics",
    "excel",
    "microsoft excel",

    "power bi",
    "tableau",
    "reporting",
    "dashboard",
    "data visualization",

    # ------------------------------------------------
    # Business / Administration
    # ------------------------------------------------
    "administration",
    "office administration",
    "filing",
    "scheduling",
    "record keeping",

    "microsoft office",
    "word",
    "powerpoint",
    "outlook",

    "inventory",
    "procurement",
    "documentation",
    "customer records",

    # ------------------------------------------------
    # Customer Service / Sales
    # ------------------------------------------------
    "customer service",
    "client service",
    "sales",
    "cashier",
    "retail",
    "customer support",
    "call center",
    "communication",
    "phone etiquette",
    "problem solving",

    # ------------------------------------------------
    # Marketing / Media
    # ------------------------------------------------
    "social media",
    "digital marketing",
    "content creation",
    "seo",
    "branding",
    "copywriting",
    "graphic design",
    "canva",
    "campaign management",
    "email marketing",

    # ------------------------------------------------
    # Finance / Accounting
    # ------------------------------------------------
    "accounting",
    "bookkeeping",
    "payroll",
    "financial analysis",
    "invoicing",
    "accounts payable",
    "accounts receivable",
    "budgeting",

    # ------------------------------------------------
    # Education / Tutoring
    # ------------------------------------------------
    "teaching",
    "tutoring",
    "lesson planning",

    "mathematics",
    "biology",
    "chemistry",
    "physics",
    "english",

    "homework help",
    "classroom management",

    # ------------------------------------------------
    # Healthcare / Support
    # ------------------------------------------------
    "patient care",
    "caregiving",
    "first aid",
    "medical records",
    "healthcare support",

    # ------------------------------------------------
    # Hospitality / Tourism
    # ------------------------------------------------
    "hospitality",
    "food service",
    "bartending",
    "housekeeping",
    "front desk",
    "reservation",
    "tourism",
    "guest service",

    # ------------------------------------------------
    # General Workplace Skills
    # ------------------------------------------------
    "teamwork",
    "leadership",
    "time management",
    "critical thinking",
    "attention to detail",
    "organization",
    "adaptability",
    "professionalism",
    "research",
    "presentation",
    "writing",
}


ALIASES = {
    "node.js": "node",
    "nodejs": "node",

    "react.js": "react",
    "reactjs": "react",

    "vue.js": "vue",
    "vuejs": "vue",

    "js": "javascript",

    "apis": "api",

    "restful": "rest api",
    "restful api": "rest api",

    "springboot": "spring boot",

    "postgres": "postgresql",

    "ms office": "microsoft office",

    "microsoft word": "word",
    "ms word": "word",

    "ms excel": "microsoft excel",

    "excel spreadsheet": "excel",

    "customer care": "customer service",

    "client support": "customer support",

    "ai imaging": "ai",

    "artificial intelligence": "ai",
}


NOISE_SKILLS = {
    "job",
    "jobs",
    "work",
    "working",
    "role",
    "roles",
    "company",
    "professional",
    "services",
    "solutions",
    "jamaica",
    "kingston",
    "mandeville",
    "montego bay",
    "based",
    "required",
    "preferred",
    "candidate",
    "application",
    "applications",
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    for old, new in ALIASES.items():
        text = text.replace(old, new)
    text = re.sub(r"[^a-z0-9\s\+\#\.\-]", " ", text)
    text = text.replace(".", " ")
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_skills_from_text(text: str):
    cleaned = clean_text(text)
    padded_text = f" {cleaned} "
    found = set()
    for skill in KNOWN_SKILLS:
        skill_clean = clean_text(skill)
        if not skill_clean or skill_clean in NOISE_SKILLS:
            continue
        if f" {skill_clean} " in padded_text:
            found.add(skill_clean)
    return sorted(found)
