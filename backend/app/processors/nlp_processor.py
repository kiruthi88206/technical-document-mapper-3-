import uuid
from datetime import datetime
from typing import Dict, Any, List
import networkx as nx

from ..database import get_db
from ..models import Document, DocumentChunk, Terminology, Concept, Relationship, ProcessingJob
from .terminology_extractor import TerminologyExtractor
from .definition_extractor import DefinitionExtractor
from .relationship_extractor import RelationshipExtractor
from ..services.document_extractor import DocumentExtractor

CATEGORY_KEYWORDS = {
    "Architecture": ["architecture", "pipeline", "framework", "microservice", "infrastructure", "stack", "system", "client", "server", "broker", "mesh"],
    "Model & Learning": ["model", "learning", "neural", "network", "transformer", "deep", "bert", "gpt", "classifier", "regression", "training", "supervised", "unsupervised"],
    "Data & Storage": ["data", "dataset", "embedding", "database", "vector", "cache", "feature", "token", "corpus", "storage", "sql", "nosql"],
    "Algorithm & Logic": ["algorithm", "optimization", "attention", "gradient", "backpropagation", "loss", "activation", "heuristic", "function", "logic"],
    "Evaluation & Metric": ["metric", "accuracy", "f1", "precision", "recall", "latency", "throughput", "score", "benchmark", "evaluation", "perplexity"],
    "Component & System": ["component", "module", "service", "encoder", "decoder", "interface", "api", "endpoint", "gateway", "layer", "node", "engine"]
}

def determine_category(term_name: str) -> str:
    name_lower = term_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in name_lower for k in keywords):
            return category
    return "General Concept"


class DocumentNLPProcessor:
    """
    Complete pipeline orchestrator:
    1. Loads document and chunks from database.
    2. Runs terminology extraction & ranking.
    3. Runs definition extraction for every term.
    4. Creates Concepts with categories.
    5. Runs directed relationship extraction between concepts.
    6. Computes graph centrality via NetworkX.
    7. Persists everything to SQLAlchemy and updates ProcessingJob state.
    """

    @classmethod
    def process_document(
        cls,
        document_id: str,
        job_id: str = None,
        max_terms: int = 40,
        min_freq: int = 1
    ) -> Dict[str, Any]:
        session = get_db()
        doc = session.query(Document).filter_by(id=document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found.")

        # Find or create job
        job = None
        if job_id:
            job = session.query(ProcessingJob).filter_by(id=job_id).first()
        if not job:
            job = ProcessingJob(
                document_id=doc.id,
                status="processing",
                progress_percent=10,
                current_stage="nlp_initialization",
                stage_message="Starting NLP document analysis"
            )
            session.add(job)
            session.commit()

        try:
            # 1. Update job stage
            doc.status = "processing"
            job.status = "processing"
            job.progress_percent = 20
            job.current_stage = "text_preparation"
            job.stage_message = "Preparing chunks and sentences"
            session.commit()

            # Retrieve chunks
            chunks = session.query(DocumentChunk).filter_by(document_id=doc.id).order_by(DocumentChunk.chunk_index).all()
            chunk_dicts = [c.to_dict() for c in chunks]

            # Reconstruct sentences from chunks
            full_text = "\n\n".join([c.text for c in chunks])
            sentences = DocumentExtractor._split_into_sentences(full_text)
            if not sentences and full_text.strip():
                sentences = [s.strip() for s in full_text.split("\n") if len(s.strip()) > 10]

            # 2. Extract Terminology
            job.progress_percent = 40
            job.current_stage = "terminology_extraction"
            job.stage_message = "Extracting technical terminology candidates"
            session.commit()

            extracted_terms = TerminologyExtractor.extract_and_rank(
                text=full_text,
                sentences=sentences,
                chunks=chunk_dicts,
                top_k=max_terms,
                min_freq=min_freq
            )

            # Clean old records if reprocessing
            session.query(Relationship).filter_by(document_id=doc.id).delete()
            session.query(Concept).filter_by(document_id=doc.id).delete()
            session.query(Terminology).filter_by(document_id=doc.id).delete()
            session.commit()

            # 3. Extract Definitions & Create Concepts
            job.progress_percent = 60
            job.current_stage = "definition_extraction"
            job.stage_message = "Detecting explicit and contextual definitions"
            session.commit()

            term_objs = []
            concept_objs = []
            concept_meta_list = []

            for t_data in extracted_terms:
                term_str = t_data["term"]
                def_res = DefinitionExtractor.extract_definition_for_term(term_str, sentences)

                # Terminology record
                term_id = str(uuid.uuid4())
                term_record = Terminology(
                    id=term_id,
                    document_id=doc.id,
                    term=term_str,
                    normalized_term=t_data["normalized_term"],
                    definition=def_res["definition"],
                    definition_type=def_res["definition_type"],
                    source_sentence=def_res["source_sentence"] or t_data.get("source_sentence", ""),
                    page_number=t_data.get("page_number", 1),
                    section_heading=t_data.get("section_heading", ""),
                    frequency=t_data["frequency"],
                    confidence_score=t_data["confidence_score"],
                    extraction_method=t_data["extraction_method"]
                )
                term_objs.append(term_record)

                # Concept record
                concept_id = str(uuid.uuid4())
                category = determine_category(term_str)
                concept_record = Concept(
                    id=concept_id,
                    document_id=doc.id,
                    name=term_str,
                    normalized_name=t_data["normalized_term"],
                    category=category,
                    description=def_res["source_sentence"] or t_data.get("source_sentence", ""),
                    definition=def_res["definition"],
                    frequency=t_data["frequency"],
                    confidence_score=t_data["confidence_score"],
                    centrality_score=0.0
                )
                concept_objs.append(concept_record)
                concept_meta_list.append({
                    "id": concept_id,
                    "name": term_str,
                    "normalized_name": t_data["normalized_term"],
                    "category": category,
                    "frequency": t_data["frequency"],
                    "confidence_score": t_data["confidence_score"]
                })

            session.add_all(term_objs)
            session.add_all(concept_objs)
            session.commit()

            # 4. Extract Relationships
            job.progress_percent = 80
            job.current_stage = "relationship_extraction"
            job.stage_message = "Discovering directed concept relationships"
            session.commit()

            extracted_rels = RelationshipExtractor.extract_relationships(
                concepts=concept_meta_list,
                sentences=sentences,
                chunks=chunk_dicts,
                min_confidence=0.45
            )

            rel_objs = []
            for r_data in extracted_rels:
                rel_id = str(uuid.uuid4())
                rel_record = Relationship(
                    id=rel_id,
                    document_id=doc.id,
                    source_concept_id=r_data["source_concept_id"],
                    target_concept_id=r_data["target_concept_id"],
                    relation_type=r_data["relation_type"],
                    confidence_score=r_data["confidence_score"],
                    supporting_sentence=r_data["supporting_sentence"],
                    source_page=r_data["source_page"],
                    source_section=r_data["source_section"],
                    extraction_method=r_data["extraction_method"],
                    is_directed=r_data["is_directed"]
                )
                rel_objs.append(rel_record)

            session.add_all(rel_objs)
            session.commit()

            # 5. Compute Network Centrality Scores
            try:
                G = nx.DiGraph()
                for c in concept_objs:
                    G.add_node(c.id)
                for r in rel_objs:
                    G.add_edge(r.source_concept_id, r.target_concept_id)

                degree_dict = nx.degree_centrality(G)
                for c in concept_objs:
                    c.centrality_score = float(degree_dict.get(c.id, 0.0))
                session.commit()
            except Exception:
                pass

            # 6. Finalize Document & Job Status
            doc.total_terms = len(term_objs)
            doc.total_concepts = len(concept_objs)
            doc.total_relationships = len(rel_objs)
            doc.processed_date = datetime.utcnow()
            doc.status = "completed_with_warnings" if doc.warning_message else "completed"

            job.status = doc.status
            job.progress_percent = 100
            job.current_stage = "completed"
            job.stage_message = f"Analysis complete: {len(concept_objs)} concepts, {len(rel_objs)} relationships extracted."
            session.commit()

            return {
                "document_id": doc.id,
                "status": doc.status,
                "total_terms": doc.total_terms,
                "total_concepts": doc.total_concepts,
                "total_relationships": doc.total_relationships,
                "warning_message": doc.warning_message
            }

        except Exception as e:
            session.rollback()
            doc.status = "failed"
            doc.error_message = str(e)
            if job:
                job.status = "failed"
                job.error_details = str(e)
                job.stage_message = f"Processing failed: {str(e)}"
            session.commit()
            raise
