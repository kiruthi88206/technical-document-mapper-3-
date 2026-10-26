import os
import re

class DocumentProcessor:
    @staticmethod
    def extract_text(file_path, file_type):
        """Extract clean text from PDF, DOCX, or TXT document."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_type.lower().strip('.')
        text = ""

        if ext == 'txt':
            text = DocumentProcessor._extract_txt(file_path)
        elif ext == 'pdf':
            text = DocumentProcessor._extract_pdf(file_path)
        elif ext == 'docx':
            text = DocumentProcessor._extract_docx(file_path)
        else:
            # Fallback text reading
            text = DocumentProcessor._extract_txt(file_path)

        text = DocumentProcessor._clean_raw_text(text)
        if not text or len(text.strip()) == 0:
            raise ValueError("Extracted text is empty or corrupted.")
        
        return text

    @staticmethod
    def _extract_txt(file_path):
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except Exception:
                continue
        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore')

    @staticmethod
    def _extract_pdf(file_path):
        text = ""
        # Try pypdf first
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            if text.strip():
                return text
        except Exception as e:
            print(f"[DocumentProcessor] pypdf warning: {e}")

        # Fallback pdfplumber or raw string parsing
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            if text.strip():
                return text
        except Exception as e:
            print(f"[DocumentProcessor] pdfplumber warning: {e}")

        # Basic fallback for pdf binary extraction if tools fail
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode('latin-1', errors='ignore')
                strings = re.findall(r'\((.*?)\)', content)
                return " ".join([s for s in strings if len(s) > 3])
        except Exception:
            return ""

    @staticmethod
    def _extract_docx(file_path):
        try:
            import docx
            doc = docx.Document(file_path)
            fullText = []
            for para in doc.paragraphs:
                if para.text:
                    fullText.append(para.text)
            return '\n'.join(fullText)
        except Exception as e:
            print(f"[DocumentProcessor] docx warning: {e}")
            return DocumentProcessor._extract_txt(file_path)

    @staticmethod
    def _clean_raw_text(text):
        if not text:
            return ""
        # Normalize whitespace and control characters
        text = re.sub(r'[\r\t]', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
