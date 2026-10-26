import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

class Config:
    PROJECT_NAME = "Technical Document Terminology and Concept Relationship Mapper"
    VERSION = "2.0.0"
    SECRET_KEY = os.environ.get("SECRET_KEY", "tech-doc-mapper-secret-key-2026")
    
    # SQLite Database URI (Migratable to PostgreSQL via env var)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{INSTANCE_DIR / 'tech_mapper.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    UPLOAD_FOLDER = str(UPLOAD_DIR)
    EXPORT_FOLDER = str(EXPORT_DIR)
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 25)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}
    
    # NLP & Pipeline Settings
    MAX_TERMS_DEFAULT = int(os.environ.get("MAX_TERMS_DEFAULT", 40))
    MIN_TERM_FREQ = int(os.environ.get("MIN_TERM_FREQ", 1))
    CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", 0.35))
    CHUNK_SIZE_WORDS = int(os.environ.get("CHUNK_SIZE_WORDS", 350))
    
    # AI / External LLM settings (Optional)
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
