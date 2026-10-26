import os
import sys
import io
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import create_app
from backend.app.database import init_db, db_session
from backend.app.services.document_extractor import DocumentExtractor
from backend.app.processors.terminology_extractor import TerminologyExtractor
from backend.app.processors.definition_extractor import DefinitionExtractor
from backend.app.processors.relationship_extractor import RelationshipExtractor
from backend.app.processors.nlp_processor import DocumentNLPProcessor
from backend.app.models import Document, Terminology, Concept, Relationship

@pytest.fixture(scope="module")
def test_app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    with app.app_context():
        init_db()
        yield app

@pytest.fixture(scope="module")
def client(test_app):
    return test_app.test_client()

class TestDocumentExtraction:
    def test_txt_extraction(self):
        sample_path = os.path.join("sample_documents", "machine_learning_system.txt")
        assert os.path.exists(sample_path)
        data = DocumentExtractor.extract_document(sample_path, "txt")
        assert data["word_count"] > 100
        assert data["sentence_count"] >= 5
        assert len(data["chunks"]) >= 1

    def test_markdown_extraction(self):
        sample_path = os.path.join("sample_documents", "cloud_microservices.md")
        assert os.path.exists(sample_path)
        data = DocumentExtractor.extract_document(sample_path, "md")
        assert data["word_count"] > 100
        assert len(data["chunks"]) >= 1
        assert any(c["section_heading"] != "" for c in data["chunks"])

    def test_docx_extraction(self):
        sample_path = os.path.join("sample_documents", "sample_cloud_architecture.docx")
        if os.path.exists(sample_path):
            data = DocumentExtractor.extract_document(sample_path, "docx")
            assert data["word_count"] > 50
            assert len(data["chunks"]) >= 1

    def test_pdf_extraction(self):
        sample_path = os.path.join("sample_documents", "sample_deep_learning_nlp.pdf")
        if os.path.exists(sample_path):
            data = DocumentExtractor.extract_document(sample_path, "pdf")
            assert data["word_count"] > 30
            assert len(data["chunks"]) >= 1
            assert data["chunks"][0]["page_number"] >= 1

    def test_empty_document_rejection(self):
        is_valid, err, ext = DocumentExtractor.validate_upload("empty.txt", b"")
        assert is_valid is False
        assert "empty" in err.lower()

    def test_invalid_file_type_rejection(self):
        is_valid, err, ext = DocumentExtractor.validate_upload("script.exe", b"binarycontent")
        assert is_valid is False
        assert "unsupported" in err.lower()


class TestNLPProcessing:
    def test_terminology_extraction_and_deduplication(self):
        text = "Deep Learning is a subset of Machine Learning. Deep learning utilizes neural networks. Machine learning builds models."
        sentences = [
            "Deep Learning is a subset of Machine Learning.",
            "Deep learning utilizes neural networks.",
            "Machine learning builds models."
        ]
        chunks = [{"chunk_index": 1, "section_heading": "Intro", "page_number": 1, "text": text}]
        terms = TerminologyExtractor.extract_and_rank(text, sentences, chunks, top_k=10, min_freq=1)
        assert len(terms) >= 2
        # Check canonical casing normalization: shouldn't have duplicate 'Deep Learning' and 'deep learning'
        term_names = [t["normalized_term"] for t in terms]
        assert len(term_names) == len(set(term_names))

    def test_explicit_definition_extraction(self):
        sentences = [
            "Deep Learning is a type of Machine Learning based on artificial neural networks.",
            "A Neural Network is used in Deep Learning.",
            "Microservices Architecture refers to a collection of loosely coupled services."
        ]
        def1 = DefinitionExtractor.extract_definition_for_term("Deep Learning", sentences)
        assert def1["definition_type"] == "explicit_document"
        assert "is a type of" in def1["definition"].lower()
        assert def1["confidence"] >= 0.85

        def2 = DefinitionExtractor.extract_definition_for_term("Microservices Architecture", sentences)
        assert def2["definition_type"] == "explicit_document"
        assert "refers to" in def2["definition"].lower()

    def test_relationship_extraction_and_direction(self):
        concepts = [
            {"id": "c1", "name": "Deep Learning"},
            {"id": "c2", "name": "Machine Learning"},
            {"id": "c3", "name": "Neural Network"}
        ]
        sentences = [
            "Deep Learning is a type of Machine Learning.",
            "A Neural Network is used in Deep Learning."
        ]
        chunks = [{"chunk_index": 1, "section_heading": "Main", "page_number": 1, "text": " ".join(sentences)}]
        rels = RelationshipExtractor.extract_relationships(concepts, sentences, chunks)
        assert len(rels) >= 2
        
        # Verify directed relation: Deep Learning -> IS_A -> Machine Learning
        is_a_rel = next((r for r in rels if r["relation_type"] == "IS_A"), None)
        assert is_a_rel is not None
        assert is_a_rel["source_name"] == "Deep Learning"
        assert is_a_rel["target_name"] == "Machine Learning"
        assert is_a_rel["is_directed"] is True
        assert len(is_a_rel["supporting_sentence"]) > 10


class TestAPIFlowAndExports:
    def test_upload_and_process_pipeline(self, client):
        sample_path = os.path.join("sample_documents", "machine_learning_system.txt")
        with open(sample_path, "rb") as f:
            file_bytes = f.read()

        # 1. Upload
        resp = client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(file_bytes), "machine_learning_system.txt")},
            content_type="multipart/form-data"
        )
        assert resp.status_code == 201
        doc_data = resp.get_json()["document"]
        doc_id = doc_data["id"]

        # 2. Process
        proc_resp = client.post(f"/api/documents/{doc_id}/process", json={"max_terms": 25})
        assert proc_resp.status_code == 200
        proc_data = proc_resp.get_json()["data"]
        assert proc_data["total_concepts"] > 5
        assert proc_data["total_relationships"] > 0

        # 3. Status
        stat_resp = client.get(f"/api/documents/{doc_id}/status")
        assert stat_resp.status_code == 200
        assert stat_resp.get_json()["status"] in ["completed", "completed_with_warnings"]

        # 4. Graph endpoint
        graph_resp = client.get(f"/api/documents/{doc_id}/graph")
        assert graph_resp.status_code == 200
        graph_data = graph_resp.get_json()
        assert len(graph_data["nodes"]) > 5
        assert len(graph_data["edges"]) > 0
        assert "x" in graph_data["nodes"][0]["position"]

        # 5. Search endpoint
        search_resp = client.get("/api/search?q=Learning")
        assert search_resp.status_code == 200
        search_json = search_resp.get_json()
        assert search_json["total_matches"] > 0

        # 6. Terminology list
        term_resp = client.get(f"/api/terminology?document_id={doc_id}")
        assert term_resp.status_code == 200
        assert term_resp.get_json()["total"] > 0

        # 7. Exports
        csv_resp = client.get(f"/api/documents/{doc_id}/export/terminology?format=csv")
        assert csv_resp.status_code == 200
        assert "text/csv" in csv_resp.content_type

        json_rel_resp = client.get(f"/api/documents/{doc_id}/export/relationships?format=json")
        assert json_rel_resp.status_code == 200
        assert "application/json" in json_rel_resp.content_type

        graph_export_resp = client.get(f"/api/documents/{doc_id}/export/graph")
        assert graph_export_resp.status_code == 200

        pdf_export_resp = client.get(f"/api/documents/{doc_id}/export/report")
        assert pdf_export_resp.status_code == 200
        assert "application/pdf" in pdf_export_resp.content_type
        assert len(pdf_export_resp.data) > 1000

        # 8. Dashboard stats
        dash_resp = client.get("/api/dashboard/stats")
        assert dash_resp.status_code == 200
        dash_data = dash_resp.get_json()
        assert dash_data["metrics"]["total_documents"] >= 1
        assert dash_data["metrics"]["total_concepts"] >= 5
