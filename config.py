import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if present
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "tech-doc-mapper-secret-key-2026")
    
    # Upload and Export directories
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    EXPORT_FOLDER = os.getenv("EXPORT_FOLDER", str(BASE_DIR / "exports"))
    SAMPLE_FOLDER = os.getenv("SAMPLE_FOLDER", str(BASE_DIR / "sample_documents"))
    LOCAL_DB_FOLDER = os.getenv("LOCAL_DB_FOLDER", str(BASE_DIR / "database" / "local_store"))
    
    # File limits
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 25 * 1024 * 1024))  # 25 MB
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    
    # Database Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "technical_doc_mapper")
    USE_MONGODB = os.getenv("USE_MONGODB", "true").lower() in ("true", "1", "yes")
    
    # NLP and Graph settings
    MAX_CONCEPTS_DEFAULT = int(os.getenv("MAX_CONCEPTS", "30"))
    SEMANTIC_SIMILARITY_THRESHOLD = float(os.getenv("SEMANTIC_SIMILARITY_THRESHOLD", "0.62"))
    COOCCURRENCE_WINDOW_SIZE = int(os.getenv("COOCCURRENCE_WINDOW_SIZE", "1"))  # sentences
    ENABLE_SENTENCE_TRANSFORMERS = os.getenv("ENABLE_SENTENCE_TRANSFORMERS", "false").lower() in ("true", "1", "yes")
    
    # Create required runtime directories
    for folder in [UPLOAD_FOLDER, EXPORT_FOLDER, SAMPLE_FOLDER, LOCAL_DB_FOLDER]:
        os.makedirs(folder, exist_ok=True)
