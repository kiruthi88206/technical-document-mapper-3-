"""
Automated End-to-End System Test for Technical Document Mapper.
Tests database, document extraction, NLP processing, relationship detection,
graph construction, PDF report generation, and Flask endpoints.
"""
import os
import sys
import json

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config import Config
from database.db import db_manager
from services.document_extractor import DocumentExtractor
from services.nlp_service import nlp_processor
from graph.relationship_detector import relationship_detector
from graph.graph_builder import KnowledgeGraphBuilder
from services.pdf_generator import PDFReportGenerator
from app import create_app

def run_tests():
    print("=" * 60)
    print("RUNNING AUTOMATED VERIFICATION SUITE")
    print("=" * 60)

    # 1. Database Check
    print("\n[TEST 1] Database Storage...")
    db_status = db_manager.get_status()
    print(f" -> Mode: {db_status['mode']}")
    print(f" -> Database: {db_status['database_name']}")
    assert db_status['connected'] is True, "Database must be connected or in local mode"
    print(" -> PASS: Database operational.")

    # 2. Document Extraction Check
    print("\n[TEST 2] Document Extractor...")
    sample_file = os.path.join(Config.SAMPLE_FOLDER, "deep_learning_nlp_architecture.txt")
    assert os.path.exists(sample_file), f"Sample file {sample_file} not found"
    extracted = DocumentExtractor.extract_text(sample_file, "deep_learning_nlp_architecture.txt")
    print(f" -> Words extracted: {extracted['word_count']}")
    print(f" -> Sentences: {extracted['sentence_count']}")
    assert extracted['word_count'] > 50, "Should extract meaningful word count"
    assert extracted['sentence_count'] > 3, "Should extract meaningful sentences"
    print(" -> PASS: Text extraction verified.")

    # 3. NLP Term Extraction & Ranking
    print("\n[TEST 3] NLP Terminology Extraction & Ranking...")
    nlp_res = nlp_processor.process_document(extracted['text'], max_concepts=20)
    concepts = nlp_res['concepts']
    glossary = nlp_res['glossary']
    print(f" -> Extracted Concepts count: {len(concepts)}")
    print(f" -> Top 3 concepts: {[c['name'] for c in concepts[:3]]}")
    assert len(concepts) >= 5, "Should extract at least 5 concepts"
    assert len(glossary) >= 5, "Glossary must contain terms"
    print(" -> PASS: NLP extraction verified.")

    # 4. Relationship Detection
    print("\n[TEST 4] Concept Relationship Detection...")
    rels = relationship_detector.detect_relationships(concepts, nlp_res['sentences'], "NLP Paper")
    print(f" -> Detected Relationships count: {len(rels)}")
    for r in rels[:3]:
        print(f"    * {r.get('source_name', r.get('from'))} --[{r.get('relation_type')}]--> {r.get('target_name', r.get('to'))}")
    assert len(rels) > 0, "Must detect at least 1 relationship (or fallback structure)"
    print(" -> PASS: Relationship detection verified.")

    # 5. Knowledge Graph Construction
    print("\n[TEST 5] NetworkX Graph Construction & Vis.js Formatting...")
    graph = KnowledgeGraphBuilder.build_graph(concepts, rels)
    nodes = graph['nodes']
    edges = graph['edges']
    metrics = graph['metrics']
    print(f" -> Vis.js Nodes: {len(nodes)}")
    print(f" -> Vis.js Edges: {len(edges)}")
    print(f" -> Primary Hub: {metrics['primary_hub']}")
    print(f" -> Density: {metrics['density']}")
    assert len(nodes) == len(concepts), "Nodes count must match concepts count"
    assert len(edges) == len(rels), "Edges count must match relationships count"
    print(" -> PASS: Graph construction verified.")

    # 6. PDF Report Generation
    print("\n[TEST 6] PDF Report Generation...")
    pdf_filename = "test_verification_report.pdf"
    pdf_path = PDFReportGenerator.generate_report(
        document_meta=extracted,
        concepts=concepts,
        relationships=rels,
        glossary=glossary,
        graph_metrics=metrics,
        output_filename=pdf_filename
    )
    assert os.path.exists(pdf_path), "PDF file should exist on disk"
    assert os.path.getsize(pdf_path) > 1000, "PDF file must not be empty"
    print(f" -> Generated PDF at: {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")
    print(" -> PASS: PDF Report Generation verified.")

    # 7. Flask Test Client Endpoints
    print("\n[TEST 7] Flask REST API Endpoints...")
    app = create_app()
    client = app.test_client()

    # Health
    res = client.get('/health')
    assert res.status_code == 200, f"Health check failed with {res.status_code}"

    # Status
    res = client.get('/api/status')
    assert res.status_code == 200, f"Status check failed with {res.status_code}"

    # Load Sample
    res = client.post('/api/sample/nlp_architecture')
    assert res.status_code == 201, f"Load sample failed with {res.status_code}"
    sample_data = json.loads(res.data)
    doc_id = sample_data['doc_id']
    print(f" -> Loaded sample doc_id: {doc_id}")

    # Analyze
    res = client.post('/api/analyze', json={'doc_id': doc_id})
    assert res.status_code == 200, f"Analyze failed with {res.status_code}"
    analyze_data = json.loads(res.data)
    assert 'graph' in analyze_data, "Graph must be in response"
    assert len(analyze_data['graph']['nodes']) > 0, "Nodes must not be empty"
    assert len(analyze_data['graph']['edges']) > 0, "Edges must not be empty"
    print(f" -> Graph contains {len(analyze_data['graph']['nodes'])} nodes and {len(analyze_data['graph']['edges'])} edges")

    # Get Graph
    res = client.get(f'/api/graph/{doc_id}')
    assert res.status_code == 200, "Get graph failed"

    # Get Glossary
    res = client.get(f'/api/glossary/{doc_id}')
    assert res.status_code == 200, "Get glossary failed"

    # Search
    res = client.get(f'/api/search?q=transformer&doc_id={doc_id}')
    assert res.status_code == 200, "Search failed"

    # Export JSON
    res = client.get(f'/api/export/{doc_id}?format=json')
    assert res.status_code == 200, "Export JSON failed"

    # Export CSV
    res = client.get(f'/api/export/{doc_id}?format=csv')
    assert res.status_code == 200, "Export CSV failed"

    # Export PDF
    res = client.get(f'/api/export/{doc_id}?format=pdf')
    assert res.status_code == 200, "Export PDF failed"

    print(" -> PASS: All REST API Endpoints verified.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! APPLICATION IS FULLY FUNCTIONAL.")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
