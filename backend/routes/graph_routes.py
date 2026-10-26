from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..routes.document_routes import uploaded_documents
from ..nlp.preprocessor import Preprocessor
from ..nlp.term_extractor import TermExtractor
from ..nlp.relationship_detector import RelationshipDetector
from ..database.graph_store import graph_store
from ..config import settings

router = APIRouter(tags=["Graph & Analysis"])

class AnalyzeRequest(BaseModel):
    document_id: str
    max_terms: Optional[int] = 35
    min_term_freq: Optional[int] = 1
    similarity_threshold: Optional[float] = 0.60

@router.post("/analyze")
async def analyze_document(request: AnalyzeRequest):
    """
    Execute full pipeline:
    1. Preprocess & sentence split
    2. Extract technical terms & rank via TF-IDF
    3. Detect relationships (co-occurrence + contextual predicates + semantic similarity)
    4. Store in graph database (Neo4j / in-memory fallback)
    5. Return interactive graph JSON
    """
    doc_id = request.document_id
    if doc_id not in uploaded_documents:
        # Check if already in graph_store
        existing = graph_store.get_graph(doc_id)
        if existing:
            return existing
        raise HTTPException(status_code=404, detail="Document ID not found. Please upload a document first.")

    raw_doc = uploaded_documents[doc_id]
    text = raw_doc["text"]
    meta = raw_doc["metadata"]

    # 1. Preprocess & segment sentences
    sentences = Preprocessor.split_sentences(text)
    if not sentences:
        raise HTTPException(
            status_code=400, 
            detail="Could not split document into readable sentences. Please check formatting."
        )

    # 2. Extract and rank technical concepts
    max_terms = request.max_terms or settings.MAX_TERMS_DEFAULT
    min_freq = request.min_term_freq or settings.MIN_TERM_FREQ
    
    concepts = TermExtractor.extract_and_rank_terms(
        text=text,
        sentences=sentences,
        top_k=max_terms,
        min_freq=min_freq
    )

    if not concepts:
        raise HTTPException(
            status_code=422,
            detail="No technical concepts could be extracted from this document. Try uploading a more specialized technical document with distinct terminology."
        )

    # 3. Detect relationships
    sim_thresh = request.similarity_threshold or settings.SIMILARITY_THRESHOLD
    edges = RelationshipDetector.detect_relationships(
        concepts=concepts,
        sentences=sentences,
        similarity_threshold=sim_thresh
    )

    # 4. Save to Graph Store and Neo4j
    graph_store.save_graph(
        doc_id=doc_id,
        metadata=meta,
        nodes=concepts,
        edges=edges
    )

    # Retrieve enriched graph structure
    result = graph_store.get_graph(doc_id)
    return result

@router.get("/graph/{document_id}")
async def get_graph(document_id: str):
    """Return graph nodes and edges for the specified document."""
    graph = graph_store.get_graph(document_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"No graph found for document ID '{document_id}'.")
    return graph

@router.get("/glossary/{document_id}")
async def get_glossary(document_id: str):
    """Return auto-generated technical glossary for the specified document."""
    glossary = graph_store.get_glossary(document_id)
    if glossary is None:
        raise HTTPException(status_code=404, detail=f"No glossary found for document ID '{document_id}'.")
    return {
        "document_id": document_id,
        "term_count": len(glossary),
        "glossary": glossary
    }

@router.get("/search")
async def search_concepts(document_id: str = Query(...), q: str = Query(...)):
    """Search extracted concepts and return matched nodes along with 1-hop connected neighbors."""
    res = graph_store.search_concepts(document_id, q)
    return res

@router.get("/documents")
async def list_documents():
    """List all analyzed documents available in the session."""
    return graph_store.list_all_documents()
