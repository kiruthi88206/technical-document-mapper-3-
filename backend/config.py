import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
SAMPLE_DOCS_DIR = BASE_DIR / "sample_docs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    # App Settings
    PROJECT_NAME: str = "Technical Document Terminology and Concept Relationship Mapper"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # Neo4j Graph DB Config
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # NLP & Extraction Settings
    MAX_TERMS_DEFAULT: int = int(os.getenv("MAX_TERMS_DEFAULT", "35"))
    MIN_TERM_FREQ: int = int(os.getenv("MIN_TERM_FREQ", "1"))
    COOCCURRENCE_WINDOW: int = int(os.getenv("COOCCURRENCE_WINDOW", "2")) # sentences
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.60"))
    
    # Storage
    UPLOAD_PATH: Path = UPLOAD_DIR
    SAMPLE_PATH: Path = SAMPLE_DOCS_DIR

settings = Settings()
