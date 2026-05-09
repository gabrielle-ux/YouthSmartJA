import os
from datetime import timedelta

class Config:
    # 1. Database - PostgreSQL connection string
    # Format: postgresql://user:password@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://youthJA_admin:youthJA123@localhost/YouthSmartJA').replace('postgres://', 'postgresql://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 2. JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-for-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # 3. RapidAPI Configuration (for your ingestion scripts)
    RAPIDAPI_KEY = "a40f668125msh607e60737cc3d96p1d1220jsn6475fb023e24"
    RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
    SEARCH_URL = "https://jsearch.p.rapidapi.com/search"
    DETAILS_URL = "https://jsearch.p.rapidapi.com/job-details"

    # 4. n8n & External Tools
    N8N_WEBHOOK_URL = os.getenv(
        "N8N_WEBHOOK_URL",
        "http://localhost:5678/webhook-test/100fbd70-b636-4445-93de-6c98f4540346"
    )

    # 5. File Upload Config
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {"pdf", "docx"}
