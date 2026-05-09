# text_cleaning.py
# Shared text-normalization rules for resume ingestion and job matching.
#
# Previously EXTRA_NOISE_WORDS, TECH_NORMALIZATION, and clean_text() were
# duplicated across cosine_matcher.py and resume_tools.py. The two copies
# had drifted (resume_tools had api/apis rules; cosine_matcher had js/flaskapi
# rules), which meant resume uploads and job matching could disagree on the
# normalized form of the same text. Centralizing here makes that impossible.

import re


EXTRA_NOISE_WORDS = {
    # Document boilerplate
    "resume", "curriculum", "vitae", "cv",
    "summary", "profile", "objective", "references",
    "project", "projects", "skill", "skills",

    # Verbs that appear everywhere in resumes and job posts
    "using", "used", "build", "built", "developed", "development",
    "work", "worked", "experience", "responsible", "including",

    # Contact-info noise
    "email", "phone", "address", "contact", "portfolio",
    "github", "linkedin", "www", "http", "https", "com",
    "name",

    # Sample-resume artifacts (keep these so demo data doesn't pollute matches)
    "alex", "johnson", "alexdev",
}


# Normalizes spelling/casing variants to a single canonical form.
# Merged union of the rules previously duplicated across two files.
TECH_NORMALIZATION = {
    "nodejs": "node",
    "node.js": "node",
    "reactjs": "react",
    "react.js": "react",
    "js": "javascript",
    "javascript": "javascript",   # explicit passthrough for clarity
    "py": "python",
    "postgres": "postgresql",
    "flaskapi": "flask api",
    "api's": "api",
    "apis": "api",
}
def clean_text(s: str) -> str:
    """
    Normalize a document for TF-IDF comparison.

      1. Lowercase.
      2. Apply tech-term normalization.
      3. Strip non-alphanumeric except + # . -
      4. Split dots/dashes into spaces.
      5. Drop tokens that are too short, pure digits, or noise words.
         Important: allow short valid skill tokens like "ai".
    """
    if not s:
        return ""

    SHORT_ALLOWED_TOKENS = {"ai", "r", "c", "c#", "go"}

    s = s.lower()

    for old, new in TECH_NORMALIZATION.items():
        s = re.sub(rf"(?<!\w){re.escape(old)}(?!\w)", new, s)

    s = re.sub(r"[^a-z0-9\s\+\#\.\-]", " ", s)
    s = s.replace(".", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s).strip()

    cleaned_tokens = []
    for token in s.split():
        if len(token) <= 2 and token not in SHORT_ALLOWED_TOKENS:
            continue
        if token.isdigit():
            continue
        if token in EXTRA_NOISE_WORDS:
            continue
        cleaned_tokens.append(token)

    return " ".join(cleaned_tokens)
