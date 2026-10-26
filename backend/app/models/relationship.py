import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from ..database import Base

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    source_concept_id = Column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    target_concept_id = Column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    relation_type = Column(String(50), nullable=False, default="RELATED_TO")  # IS_A, PART_OF, USES, DEPENDS_ON, RELATED_TO, etc.
    confidence_score = Column(Float, nullable=False, default=0.5)
    supporting_sentence = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=True, default=1)
    source_section = Column(String(255), nullable=True, default="")
    extraction_method = Column(String(100), nullable=False, default="predicate_grammar")
    is_directed = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="relationships")
    source_concept = relationship("Concept", foreign_keys=[source_concept_id], back_populates="outgoing_relationships")
    target_concept = relationship("Concept", foreign_keys=[target_concept_id], back_populates="incoming_relationships")

    __table_args__ = (
        Index("ix_rel_doc_src_tgt", "document_id", "source_concept_id", "target_concept_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "source_concept_id": self.source_concept_id,
            "target_concept_id": self.target_concept_id,
            "source_name": self.source_concept.name if self.source_concept else "Unknown",
            "target_name": self.target_concept.name if self.target_concept else "Unknown",
            "relation_type": self.relation_type,
            "confidence_score": round(self.confidence_score, 3),
            "supporting_sentence": self.supporting_sentence,
            "source_page": self.source_page,
            "source_section": self.source_section,
            "extraction_method": self.extraction_method,
            "is_directed": self.is_directed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
