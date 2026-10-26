import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from ..database import Base

class Terminology(Base):
    __tablename__ = "terminologies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    term = Column(String(255), nullable=False, index=True)
    normalized_term = Column(String(255), nullable=False, index=True)
    
    definition = Column(Text, nullable=True)
    definition_type = Column(String(50), default="contextual_inference")  # explicit_document, contextual_inference, ai_generated
    source_sentence = Column(Text, nullable=True)
    
    page_number = Column(Integer, nullable=True, default=1)
    section_heading = Column(String(255), nullable=True, default="")
    
    frequency = Column(Integer, nullable=False, default=1)
    confidence_score = Column(Float, nullable=False, default=0.5)
    extraction_method = Column(String(100), nullable=False, default="spacy_pos_tfidf")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="terminologies")

    __table_args__ = (
        Index("ix_term_doc_norm", "document_id", "normalized_term"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "term": self.term,
            "normalized_term": self.normalized_term,
            "definition": self.definition or "No explicit definition found in document.",
            "definition_type": self.definition_type,
            "source_sentence": self.source_sentence or "",
            "page_number": self.page_number,
            "section_heading": self.section_heading,
            "frequency": self.frequency,
            "confidence_score": round(self.confidence_score, 3),
            "extraction_method": self.extraction_method,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
