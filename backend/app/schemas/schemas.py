from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DocumentResponseSchema(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    upload_date: Optional[str] = None
    processed_date: Optional[str] = None
    total_chunks: int = 0
    total_terms: int = 0
    total_concepts: int = 0
    total_relationships: int = 0
    word_count: int = 0
    sentence_count: int = 0

class TerminologySchema(BaseModel):
    id: str
    document_id: str
    term: str
    normalized_term: str
    definition: str
    definition_type: str
    source_sentence: str
    page_number: Optional[int] = 1
    section_heading: Optional[str] = ""
    frequency: int
    confidence_score: float
    extraction_method: str

class ConceptSchema(BaseModel):
    id: str
    document_id: str
    name: str
    normalized_name: str
    category: str
    description: str
    definition: str
    frequency: int
    confidence_score: float
    centrality_score: float

class RelationshipSchema(BaseModel):
    id: str
    document_id: str
    source_concept_id: str
    target_concept_id: str
    source_name: str
    target_name: str
    relation_type: str
    confidence_score: float
    supporting_sentence: str
    source_page: Optional[int] = 1
    source_section: Optional[str] = ""
    extraction_method: str
    is_directed: bool = True

class GraphNodeData(BaseModel):
    id: str
    label: str
    category: str
    color: str
    frequency: int
    confidence_score: float
    centrality_score: float
    definition: str
    description: str
    incoming_count: int = 0
    outgoing_count: int = 0

class GraphNodeSchema(BaseModel):
    id: str
    type: str = "conceptNode"
    position: Dict[str, float]
    data: GraphNodeData

class GraphEdgeData(BaseModel):
    id: str
    relation_type: str
    confidence_score: float
    supporting_sentence: str
    source_page: Optional[int] = 1
    source_section: Optional[str] = ""
    extraction_method: str
    source_name: str
    target_name: str
    color: str

class GraphEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    type: str = "smoothstep"
    label: str
    data: GraphEdgeData
