#used to be in main.py
import re

SKILLS = [
    "python", "java", "javascript", "typescript", "react", "node", "node.js",
    "sql", "mysql", "postgresql", "docker", "kubernetes", "aws", "azure", "gcp",
    "flask", "django", "fastapi", "spring", "spring boot", ".net", "c#", "git",
    "rest", "rest api", "graphql", "microservices",
    "excel", "communication", "accounting", "quickbooks", "sage"
]

CERT_PATTERNS = [
    r"\bPMP\b", r"\bPRINCE2\b", r"\bCISSP\b",
    r"\bSix\s*Sigma\b", r"\bLean\s*Six\s*Sigma\b"
]

DEGREE_PATTERNS = [
    r"\bBSc\b", r"\bBA\b", r"\bMBA\b",
    r"\bBachelor'?s\b", r"\bMaster'?s\b", r"\bDegree\b"
]

EXP_PATTERNS = [
    r"\b(\d{1,2})\s*(?:-|–|to)\s*(\d{1,2})\s*(?:years?|yrs?)\b",
    r"\b(\d{1,2})\+?\s*(?:years?|yrs?)\b",
    r"\b(?:minimum|min\.?|at\s+least)\s+(\d{1,2})\s*(?:years?|yrs?)\b",
    r"\b(\d{1,2})\s*(?:years?|yrs?)\s+experience\b",
]

def dedupe_keep_order(items):
    seen = set()
    out = []
    for x in items:
        key = str(x).lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(x)
    return out

def extract_job_info(text: str):
    if not text:
        return {"skills": [], "certifications": [], "degrees": [], "experience": []}

    found_skills = []
    for s in SKILLS:
        pattern = r"(?<!\w)" + re.escape(s) + r"(?!\w)"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found_skills.append(s)

    found_certs = []
    for p in CERT_PATTERNS:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            found_certs.append(m.group(0))

    found_degrees = []
    for p in DEGREE_PATTERNS:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            found_degrees.append(m.group(0))

    found_exp = []
    for p in EXP_PATTERNS:
        for m in re.finditer(p, text, flags=re.IGNORECASE):
            found_exp.append(m.group(0))

    return {
        "skills": dedupe_keep_order(found_skills),
        "certifications": dedupe_keep_order(found_certs),
        "degrees": dedupe_keep_order(found_degrees),
        "experience": dedupe_keep_order(found_exp),
    }
