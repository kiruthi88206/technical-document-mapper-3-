import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.document_parser import DocumentParser
from ..database.graph_store import graph_store
from ..config import settings

router = APIRouter(tags=["Document"])

# Temporary in-memory cache for raw uploaded texts before analysis
uploaded_documents = {}

@router.get("/health")
async def health_check():
    """System health check and database connectivity status."""
    db_status = graph_store.get_database_status()
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status
    }

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Module 1: Document Ingestion
    Upload PDF, DOCX, or TXT file, validate file type, extract and normalize text.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    contents = await file.read()
    
    # 1. Validate file extension and size
    is_valid, err_msg = DocumentParser.validate_file(file.filename, contents)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    # 2. Extract and normalize text
    try:
        normalized_text = DocumentParser.extract_text(file.filename, contents)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse document text: {str(e)}")

    if not normalized_text or len(normalized_text.strip()) < 50:
        raise HTTPException(
            status_code=400, 
            detail="Document text is insufficient (less than 50 characters). Please provide a richer technical document."
        )

    # 3. Compute metrics
    metrics = DocumentParser.get_document_metrics(normalized_text)
    
    doc_id = str(uuid.uuid4())[:8]
    doc_metadata = {
        "document_id": doc_id,
        "filename": file.filename,
        "file_size_bytes": len(contents),
        **metrics
    }

    # Store raw text for analysis step
    uploaded_documents[doc_id] = {
        "metadata": doc_metadata,
        "text": normalized_text
    }

    return {
        "success": True,
        "message": "Document uploaded and parsed successfully.",
        "document_id": doc_id,
        "metadata": doc_metadata,
        "preview": normalized_text[:300] + ("..." if len(normalized_text) > 300 else "")
    }

@router.post("/sample")
async def load_sample_document(sample_type: str = "nlp_knowledge_graphs"):
    """Load a built-in comprehensive sample technical document for instant testing."""
    sample_texts = {
        "nlp_knowledge_graphs": """
# Technical Architecture: Document Terminology & Knowledge Graph Extraction

## Abstract
Modern technical document comprehension relies heavily on Natural Language Processing (NLP) and Knowledge Graphs. Dense technical literature often obscures dependencies between concepts. This document details an end-to-end architecture that ingests unstructured technical documents, extracts technical terms and noun phrases, ranks them with TF-IDF and frequency analysis, detects relational semantics via co-occurrence and sentence embeddings, and stores the resulting concept network in Neo4j.

## 1. Document Ingestion and Normalization
The ingestion pipeline supports PDF, DOCX, and TXT files. Raw text is parsed using document extractors, stripping formatting noise, repairing hyphenated line breaks, and normalizing token streams. Preprocessing splits the corpus into discrete sentences and eliminates stopwords while preserving technical compound nouns and acronyms.

## 2. Technical Term Extraction
Domain-specific terms and named entities are identified using part-of-speech tagging and noun chunking via spaCy and NLTK. Significant concepts are ranked using TF-IDF (Term Frequency-Inverse Document Frequency) vectorization. High-ranking terms represent foundational domain concepts such as TF-IDF, Knowledge Graph, Semantic Similarity, and FastAPI.

## 3. Relationship Detection Engine
Concept dependencies stay implicit without relational analysis. The relationship detection module scans sentence co-occurrence to locate grammatical predicates such as "uses", "implements", "connects to", and "depends on". Furthermore, sentence embeddings compute cosine similarity between technical terms to establish semantic similarity links. Concepts that appear in proximate contextual windows are linked to ensure comprehensive graph connectivity.

## 4. Graph Construction and Neo4j Storage
Extracted concepts are modeled as graph nodes, and detected relationships are represented as directed edges with confidence weights. Graph data is stored in the Neo4j graph database using parameterized Cypher queries. The database organizes Document nodes, Concept nodes, and RELATES_TO relationships. When a database cluster is offline, a local in-memory graph engine provides a seamless fallback.

## 5. Interactive Visualization and User Experience
The frontend is built with React.js and Tailwind CSS, utilizing vis-network.js and D3.js to render an explorable, force-directed Knowledge Graph. Users can zoom, pan, select nodes, search concepts, and inspect connected neighbors. An auto-generated glossary presents term definitions, frequency scores, and contextual excerpts. Documentation teams can export graph data as JSON, glossary entries as CSV, and download professional PDF reports.
"""
    }

    chosen_text = sample_texts.get(sample_type, sample_texts["nlp_knowledge_graphs"])
    normalized_text = DocumentParser.normalize_text(chosen_text)
    metrics = DocumentParser.get_document_metrics(normalized_text)

    doc_id = "sample-" + str(uuid.uuid4())[:6]
    doc_metadata = {
        "document_id": doc_id,
        "filename": "Sample_Technical_Architecture_KG.txt",
        "file_size_bytes": len(chosen_text.encode('utf-8')),
        **metrics
    }

    uploaded_documents[doc_id] = {
        "metadata": doc_metadata,
        "text": normalized_text
    }

    return {
        "success": True,
        "message": "Sample technical document loaded successfully.",
        "document_id": doc_id,
        "metadata": doc_metadata,
        "preview": normalized_text[:300] + "..."
    }
