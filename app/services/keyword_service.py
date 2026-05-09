# replaces upsert_job, refresh_many_kv from main

import sys
import os
import requests
import time
import random

# Fix path to see 'app' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Job, JobCert, JobDegree, JobExperience, JobSkill
from app.services.job_extraction import extract_job_info  # Your regex logic
from app.utils.text_processing import extract_skills_from_text, clean_text
from sklearn.feature_extraction.text import TfidfVectorizer

app = create_app()

# =====================================================
# HELPERS (REFACTORED FROM YOUR main.py)
# =====================================================

def build_keywords_for_docs(docs, top_n=25):
    cleaned_docs = [clean_text(d) for d in docs]
    if not any(cleaned_docs):
        return [[] for _ in docs]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
    X = vec.fit_transform(cleaned_docs)
    terms = vec.get_feature_names_out()
    keywords_list = []
    for i in range(X.shape[0]):
        row = X.getrow(i).toarray()[0]
        idx = row.argsort()[::-1][:top_n]
        kws = [terms[j] for j in idx if row[j] > 0]
        keywords_list.append(kws)
    return keywords_list