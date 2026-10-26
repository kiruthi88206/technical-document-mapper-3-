import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.document_parser import DocumentParser
from backend.nlp.preprocessor import Preprocessor
from backend.nlp.term_extractor import TermExtractor
from backend.nlp.relationship_detector import RelationshipDetector
from backend.database.graph_store import graph_store

client = TestClient(app)
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "backend" / "sample_docs"

class TestDocumentIngestion:
    """Module 1 Tests: Document Ingestion across TXT, DOCX, and PDF formats."""

    def test_extract_txt(self):
        txt_path = SAMPLE_DIR / "sample_architecture.txt"
        assert txt_path.exists(), "Sample TXT file must exist"
        with open(txt_path, "rb") as f:
            bytes_data = f.read()
        text = DocumentParser.extract_text("sample_architecture.txt", bytes_data)
        assert len(text) > 100
        assert "Knowledge Graph" in text
        metrics = DocumentParser.get_document_metrics(text)
        assert metrics["word_count"] > 50

    def test_extract_docx(self):
        docx_path = SAMPLE_DIR / "sample_cloud_architecture.docx"
        assert docx_path.exists(), "Sample DOCX file must exist"
        with open(docx_path, "rb") as f:
            bytes_data = f.read()
        text = DocumentParser.extract_text("sample_cloud_architecture.docx", bytes_data)
        assert len(text) > 50
        assert "Microservices" in text or "Kubernetes" in text
        metrics = DocumentParser.get_document_metrics(text)
        assert metrics["sentence_count"] >= 3

    def test_extract_pdf(self):
        pdf_path = SAMPLE_DIR / "sample_deep_learning_nlp.pdf"
        assert pdf_path.exists(), "Sample PDF file must exist"
        with open(pdf_path, "rb") as f:
            bytes_data = f.read()
        text = DocumentParser.extract_text("sample_deep_learning_nlp.pdf", bytes_data)
        assert len(text) > 50
        assert "Natural Language Processing" in text or "Transformer" in text

    def test_validation_errors(self):
        # Empty file
        valid, msg = DocumentParser.validate_file("empty.txt", b"")
        assert not valid
        assert "empty" in msg.lower()

        # Invalid extension
        valid, msg = DocumentParser.validate_file("malicious.exe", b"binary content")
        assert not valid
        assert "unsupported" in msg.lower()

class TestNLPExtractionAndRelationships:
    """Modules 2 & 3 Tests: Technical Term Recognition & Relationship Detection."""

    def test_term_extraction_and_ranking(self):
        sample_text = """
        Natural Language Processing systems use Knowledge Graphs to organize domain concepts.
        The TF-IDF vectorization method computes statistical importance scores for technical terminology.
        Neo4j is a graph database that stores nodes and relational edges efficiently.
        FastAPI is a modern web framework that exposes high-performance REST APIs.
        """
        sentences = Preprocessor.split_sentences(sample_text)
        assert len(sentences) >= 3

        concepts = TermExtractor.extract_and_rank_terms(sample_text, sentences, top_k=15)
        assert len(concepts) > 0
        labels = [c["label"].lower() for c in concepts]
        
        # Verify key technical terms are identified
        assert any("natural language processing" in l or "nlp" in l or "knowledge graph" in l for l in labels)
        
        # Verify TF-IDF and categorization attributes are present
        for c in concepts:
            assert "category" in c
            assert "color" in c
            assert "tfidf_score" in c
            assert "frequency" in c
            assert "definition" in c

    def test_relationship_detection(self):
        sample_text = """
        FastAPI implements a high-performance REST API.
        The REST API connects to a Neo4j graph database.
        The system uses Knowledge Graphs for semantic search.
        Knowledge Graphs depend on Natural Language Processing pipelines.
        """
        sentences = Preprocessor.split_sentences(sample_text)
        concepts = TermExtractor.extract_and_rank_terms(sample_text, sentences, top_k=10)
        edges = RelationshipDetector.detect_relationships(concepts, sentences)

        # Graph validation rules: Must never return empty edges when concepts exist
        assert len(edges) > 0, "Relationships must be generated between concepts"
        for edge in edges:
            assert "from" in edge
            assert "to" in edge
            assert "label" in edge
            assert "confidence" in edge
            assert "type" in edge

class TestAPIRoutes:
    """End-to-End API Routes Tests."""

    def test_health_endpoint(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert "database" in data

    def test_sample_load_endpoint(self):
        resp = client.post("/api/sample?sample_type=nlp_knowledge_graphs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "document_id" in data
        assert "metadata" in data
        return data["document_id"]

    def test_end_to_end_pipeline(self):
        # 1. Load document
        load_resp = client.post("/api/sample?sample_type=nlp_knowledge_graphs")
        doc_id = load_resp.json()["document_id"]

        # 2. Run analysis
        analyze_resp = client.post("/api/analyze", json={
            "document_id": doc_id,
            "max_terms": 25,
            "min_term_freq": 1,
            "similarity_threshold": 0.55
        })
        assert analyze_resp.status_code == 200
        graph_data = analyze_resp.json()
        assert "nodes" in graph_data
        assert "edges" in graph_data
        assert len(graph_data["nodes"]) > 0
        assert len(graph_data["edges"]) > 0

        # 3. Fetch Graph
        graph_resp = client.get(f"/api/graph/{doc_id}")
        assert graph_resp.status_code == 200
        assert len(graph_resp.json()["nodes"]) == len(graph_data["nodes"])

        # 4. Fetch Glossary
        gloss_resp = client.get(f"/api/glossary/{doc_id}")
        assert gloss_resp.status_code == 200
        glossary = gloss_resp.json()["glossary"]
        assert len(glossary) == len(graph_data["nodes"])

        # 5. Search Concepts
        search_resp = client.get(f"/api/search?document_id={doc_id}&q=graph")
        assert search_resp.status_code == 200
        search_data = search_resp.json()
        assert "matches" in search_data
        assert "subgraph" in search_data

        # 6. Export JSON
        export_json = client.get(f"/api/export/{doc_id}?format=json")
        assert export_json.status_code == 200
        assert export_json.headers["content-type"] == "application/json"

        # 7. Export CSV
        export_csv = client.get(f"/api/export/{doc_id}?format=csv")
        assert export_csv.status_code == 200
        assert "text/csv" in export_csv.headers["content-type"]

        # 8. Export PDF
        export_pdf = client.get(f"/api/export/pdf/{doc_id}")
        assert export_pdf.status_code == 200
        assert export_pdf.headers["content-type"] == "application/pdf"
        assert len(export_pdf.content) > 1000

    def test_upload_real_files(self):
        # Upload TXT
        txt_path = SAMPLE_DIR / "sample_architecture.txt"
        with open(txt_path, "rb") as f:
            resp = client.post("/api/upload", files={"file": ("sample.txt", f, "text/plain")})
        assert resp.status_code == 200
        doc_id = resp.json()["document_id"]
        
        # Analyze uploaded file
        res = client.post("/api/analyze", json={"document_id": doc_id})
        assert res.status_code == 200
        assert len(res.json()["nodes"]) > 0

        # Upload DOCX
        docx_path = SAMPLE_DIR / "sample_cloud_architecture.docx"
        with open(docx_path, "rb") as f:
            resp_docx = client.post("/api/upload", files={"file": ("sample.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
        assert resp_docx.status_code == 200
        
        # Upload PDF
        pdf_path = SAMPLE_DIR / "sample_deep_learning_nlp.pdf"
        with open(pdf_path, "rb") as f:
            resp_pdf = client.post("/api/upload", files={"file": ("sample.pdf", f, "application/pdf")})
        assert resp_pdf.status_code == 200

    def test_error_handling(self):
        # Missing file
        resp = client.post("/api/analyze", json={"document_id": "non-existent-id"})
        assert resp.status_code == 404

        # File with insufficient text
        resp = client.post(
            "/api/upload", 
            files={"file": ("short.txt", b"too short", "text/plain")}
        )
        assert resp.status_code == 400
        assert "insufficient" in resp.json()["detail"].lower()
