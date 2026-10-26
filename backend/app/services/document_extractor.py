import os
import re
import uuid
from pathlib import Path
from typing import Dict, Any, List, Tuple
from pypdf import PdfReader
from docx import Document as DocxDocument
from ..config import Config

class DocumentExtractor:
    """
    Robust document extraction service supporting PDF, DOCX, TXT, and Markdown (.md).
    Validates file integrity, extracts text page-by-page or section-by-section,
    segments into chunks with character offsets, and detects scanned/empty documents.
    """

    ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS

    @classmethod
    def validate_upload(cls, filename: str, file_bytes: bytes) -> Tuple[bool, str, str]:
        """
        Validate file extension and basic magic bytes.
        Returns (is_valid, error_msg, detected_ext).
        """
        if not filename or "." not in filename:
            return False, "File name must include a valid extension.", ""

        ext = filename.rsplit(".", 1)[1].lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"Unsupported file type '.{ext}'. Allowed types are: {', '.join(sorted(cls.ALLOWED_EXTENSIONS))}.", ext

        if len(file_bytes) == 0:
            return False, "The uploaded file is empty (0 bytes).", ext

        if len(file_bytes) > Config.MAX_CONTENT_LENGTH:
            max_mb = Config.MAX_CONTENT_LENGTH // (1024 * 1024)
            return False, f"File exceeds maximum allowed upload size of {max_mb} MB.", ext

        # Magic byte verification
        if ext == "pdf" and not file_bytes.startswith(b"%PDF"):
            return False, "Invalid PDF file: Missing %PDF header signature.", ext
        elif ext == "docx" and not file_bytes.startswith(b"PK"):
            return False, "Invalid DOCX file: Missing PK archive signature.", ext

        return True, "", ext

    @classmethod
    def save_uploaded_file(cls, filename: str, file_bytes: bytes) -> Tuple[str, str]:
        """
        Saves file to upload directory using a generated UUID to prevent path traversal
        and filename collisions. Returns (stored_filename, absolute_path).
        """
        ext = filename.rsplit(".", 1)[1].lower()
        safe_id = str(uuid.uuid4())
        stored_filename = f"{safe_id}.{ext}"
        target_path = Path(Config.UPLOAD_FOLDER) / stored_filename
        
        with open(target_path, "wb") as f:
            f.write(file_bytes)
            
        return stored_filename, str(target_path)

    @classmethod
    def extract_document(cls, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Extract text and section chunks from a supported document.
        Returns a dict with:
        - raw_text: full normalized text
        - chunks: list of chunk dicts
        - word_count: total word count
        - sentence_count: estimated sentence count
        - warning_message: scanned PDF warning or format notice
        """
        file_type = file_type.lower()
        if file_type == "pdf":
            return cls._extract_pdf(file_path)
        elif file_type == "docx":
            return cls._extract_docx(file_path)
        elif file_type in ("txt", "md"):
            return cls._extract_plaintext(file_path, is_markdown=(file_type == "md"))
        else:
            raise ValueError(f"Unsupported extraction format: {file_type}")

    @classmethod
    def _extract_pdf(cls, file_path: str) -> Dict[str, Any]:
        reader = PdfReader(file_path)
        num_pages = len(reader.pages)
        if num_pages == 0:
            raise ValueError("The PDF contains no pages.")

        full_text_parts = []
        chunks = []
        current_offset = 0
        pages_with_no_text = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            page_text = page_text.strip()
            if not page_text:
                pages_with_no_text += 1
                continue

            # Normalize whitespace
            normalized_page = re.sub(r'[ \t]+', ' ', page_text)
            normalized_page = re.sub(r'\n{3,}', '\n\n', normalized_page)

            start_off = current_offset
            end_off = start_off + len(normalized_page)
            current_offset = end_off + 2

            full_text_parts.append(normalized_page)

            # Look for page header or first line
            first_line = normalized_page.split("\n", 1)[0][:100].strip()
            section_title = first_line if len(first_line) > 3 and len(first_line) < 80 else f"Page {page_idx}"

            words = normalized_page.split()
            chunks.append({
                "chunk_index": len(chunks) + 1,
                "section_heading": section_title,
                "page_number": page_idx,
                "start_offset": start_off,
                "end_offset": end_off,
                "text": normalized_page,
                "token_count": len(words)
            })

        full_text = "\n\n".join(full_text_parts)
        words = full_text.split()
        sentences = cls._split_into_sentences(full_text)

        warning = ""
        if len(words) == 0:
            raise ValueError(
                "No readable text could be extracted from this PDF. "
                "This document appears to be a scanned image or raster PDF. "
                "OCR (Optical Character Recognition) is not enabled; please provide a document with an embedded text layer."
            )
        elif pages_with_no_text > 0:
            warning = f"Notice: {pages_with_no_text} of {num_pages} page(s) contained no selectable text layer (may be scanned images or diagrams)."

        return {
            "raw_text": full_text,
            "chunks": chunks,
            "word_count": len(words),
            "sentence_count": len(sentences),
            "warning_message": warning
        }

    @classmethod
    def _extract_docx(cls, file_path: str) -> Dict[str, Any]:
        doc = DocxDocument(file_path)
        chunks = []
        full_text_parts = []
        current_offset = 0

        current_heading = "Introduction"
        current_paragraph_buffer = []
        current_words = 0

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style_name = para.style.name.lower() if para.style else ""
            is_heading = "heading" in style_name or (len(text) < 70 and para.runs and para.runs[0].bold)

            if is_heading:
                # Flush previous paragraph buffer
                if current_paragraph_buffer:
                    chunk_text = "\n\n".join(current_paragraph_buffer)
                    start_off = current_offset
                    end_off = start_off + len(chunk_text)
                    current_offset = end_off + 2
                    full_text_parts.append(chunk_text)
                    chunks.append({
                        "chunk_index": len(chunks) + 1,
                        "section_heading": current_heading,
                        "page_number": 1,
                        "start_offset": start_off,
                        "end_offset": end_off,
                        "text": chunk_text,
                        "token_count": current_words
                    })
                    current_paragraph_buffer = []
                    current_words = 0
                current_heading = text
            else:
                current_paragraph_buffer.append(text)
                current_words += len(text.split())
                
                # Check if buffer reached chunk size threshold
                if current_words >= Config.CHUNK_SIZE_WORDS:
                    chunk_text = "\n\n".join(current_paragraph_buffer)
                    start_off = current_offset
                    end_off = start_off + len(chunk_text)
                    current_offset = end_off + 2
                    full_text_parts.append(chunk_text)
                    chunks.append({
                        "chunk_index": len(chunks) + 1,
                        "section_heading": current_heading,
                        "page_number": 1,
                        "start_offset": start_off,
                        "end_offset": end_off,
                        "text": chunk_text,
                        "token_count": current_words
                    })
                    current_paragraph_buffer = []
                    current_words = 0

        # Flush any trailing buffer
        if current_paragraph_buffer:
            chunk_text = "\n\n".join(current_paragraph_buffer)
            start_off = current_offset
            end_off = start_off + len(chunk_text)
            full_text_parts.append(chunk_text)
            chunks.append({
                "chunk_index": len(chunks) + 1,
                "section_heading": current_heading,
                "page_number": 1,
                "start_offset": start_off,
                "end_offset": end_off,
                "text": chunk_text,
                "token_count": current_words
            })

        full_text = "\n\n".join(full_text_parts)
        words = full_text.split()
        if len(words) < 5:
            raise ValueError("The DOCX document contains insufficient readable text (fewer than 5 words).")

        return {
            "raw_text": full_text,
            "chunks": chunks,
            "word_count": len(words),
            "sentence_count": len(cls._split_into_sentences(full_text)),
            "warning_message": ""
        }

    @classmethod
    def _extract_plaintext(cls, file_path: str, is_markdown: bool = False) -> Dict[str, Any]:
        # Try UTF-8 first, fallback to latin-1
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

        normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
        words = normalized.split()
        if len(words) < 5:
            raise ValueError("The text document contains insufficient readable text (fewer than 5 words).")

        chunks = []
        full_text_parts = []
        current_offset = 0

        # Split markdown by headings or split plain text by double newlines
        if is_markdown:
            sections = re.split(r'\n(?=#{1,3}\s+)', normalized)
        else:
            sections = normalized.split("\n\n")

        current_heading = "Main"
        current_buffer = []
        current_word_count = 0

        for sec in sections:
            sec_clean = sec.strip()
            if not sec_clean:
                continue

            if is_markdown and sec_clean.startswith("#"):
                first_line, *rest = sec_clean.split("\n", 1)
                heading_match = re.match(r'^(#{1,3})\s+(.*)$', first_line)
                if heading_match:
                    current_heading = heading_match.group(2).strip()
                    sec_clean = rest[0].strip() if rest else ""

            if not sec_clean:
                continue

            sec_words = len(sec_clean.split())
            if current_word_count + sec_words >= Config.CHUNK_SIZE_WORDS and current_buffer:
                chunk_text = "\n\n".join(current_buffer)
                start_off = current_offset
                end_off = start_off + len(chunk_text)
                current_offset = end_off + 2
                full_text_parts.append(chunk_text)
                chunks.append({
                    "chunk_index": len(chunks) + 1,
                    "section_heading": current_heading,
                    "page_number": 1,
                    "start_offset": start_off,
                    "end_offset": end_off,
                    "text": chunk_text,
                    "token_count": current_word_count
                })
                current_buffer = [sec_clean]
                current_word_count = sec_words
            else:
                current_buffer.append(sec_clean)
                current_word_count += sec_words

        if current_buffer:
            chunk_text = "\n\n".join(current_buffer)
            start_off = current_offset
            end_off = start_off + len(chunk_text)
            full_text_parts.append(chunk_text)
            chunks.append({
                "chunk_index": len(chunks) + 1,
                "section_heading": current_heading,
                "page_number": 1,
                "start_offset": start_off,
                "end_offset": end_off,
                "text": chunk_text,
                "token_count": current_word_count
            })

        full_text = "\n\n".join(full_text_parts) if full_text_parts else normalized
        return {
            "raw_text": full_text,
            "chunks": chunks,
            "word_count": len(words),
            "sentence_count": len(cls._split_into_sentences(full_text)),
            "warning_message": ""
        }

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        raw = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'`])', text)
        return [s.strip() for s in raw if len(s.strip()) > 15]
