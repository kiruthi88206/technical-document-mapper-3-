"""
Document Extraction Service
Handles text extraction from PDF, DOCX, and TXT files with full metadata extraction,
format validation, and error handling.
"""
import os
import re
from typing import Dict, Any, Tuple
from config import Config

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class DocumentExtractor:
    """Extracts text and metadata from supported technical document formats."""

    @staticmethod
    def validate_file(filename: str, file_size: int) -> Tuple[bool, str]:
        """Validate file extension and size."""
        if not filename or "." not in filename:
            return False, "Invalid filename or missing extension."
        
        ext = filename.rsplit(".", 1)[1].lower()
        if ext not in Config.ALLOWED_EXTENSIONS:
            allowed = ", ".join(Config.ALLOWED_EXTENSIONS)
            return False, f"Unsupported file type '.{ext}'. Supported types: {allowed}"
        
        if file_size > Config.MAX_CONTENT_LENGTH:
            max_mb = Config.MAX_CONTENT_LENGTH // (1024 * 1024)
            return False, f"File size exceeds the {max_mb}MB limit."
        
        return True, "Valid"

    @classmethod
    def extract_text(cls, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Extract clean text and structural metadata from the file.
        Returns a dictionary with raw text, page count, word count, character count, and status.
        """
        ext = filename.rsplit(".", 1)[1].lower()
        extracted_text = ""
        page_count = 1
        meta_info = {}

        if ext == "txt":
            extracted_text, meta_info = cls._extract_txt(file_path)
        elif ext == "pdf":
            extracted_text, page_count, meta_info = cls._extract_pdf(file_path)
        elif ext == "docx":
            extracted_text, page_count, meta_info = cls._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported format: .{ext}")

        # Post-clean extracted text
        cleaned_text = cls.clean_text(extracted_text)
        
        if not cleaned_text.strip():
            raise ValueError("The uploaded document contains no readable text or is empty.")

        words = re.findall(r'\b\w+\b', cleaned_text)
        word_count = len(words)
        char_count = len(cleaned_text)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned_text) if s.strip()]
        sentence_count = len(sentences)

        # Estimate reading time (average 200 wpm)
        reading_time_min = max(1, round(word_count / 200))

        return {
            "text": cleaned_text,
            "filename": filename,
            "file_type": ext.upper(),
            "file_size": os.path.getsize(file_path),
            "page_count": page_count,
            "word_count": word_count,
            "char_count": char_count,
            "sentence_count": sentence_count,
            "estimated_reading_time_min": reading_time_min,
            "metadata": meta_info
        }

    @staticmethod
    def _extract_txt(file_path: str) -> Tuple[str, Dict[str, Any]]:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    text = f.read()
                return text, {"encoding": enc}
            except (UnicodeDecodeError, Exception):
                continue
        raise ValueError("Could not decode TXT file with standard encodings.")

    @staticmethod
    def _extract_pdf(file_path: str) -> Tuple[str, int, Dict[str, Any]]:
        if not PYPDF_AVAILABLE:
            raise RuntimeError("pypdf library is required to parse PDF files.")
        
        reader = PdfReader(file_path)
        num_pages = len(reader.pages)
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text:
                text_parts.append(page_text)
        
        full_text = "\n\n".join(text_parts)
        doc_info = {}
        if reader.metadata:
            for k, v in reader.metadata.items():
                if v:
                    doc_info[str(k).replace("/", "")] = str(v)
                    
        return full_text, num_pages, doc_info

    @staticmethod
    def _extract_docx(file_path: str) -> Tuple[str, int, Dict[str, Any]]:
        if not DOCX_AVAILABLE:
            raise RuntimeError("python-docx library is required to parse DOCX files.")
        
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)
        
        # Approximate pages by paragraph count (~5 paragraphs per page average)
        estimated_pages = max(1, len(paragraphs) // 5)
        return full_text, estimated_pages, {"paragraph_count": len(paragraphs)}

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Strip non-printable characters, weird line breaks, and excessive spacing."""
        if not raw_text:
            return ""
        # Normalize newlines
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace multiple spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Normalize excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
