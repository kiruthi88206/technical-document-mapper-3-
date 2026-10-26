import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from ..database import Base

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, default="General")
    description = Column(Text, nullable=True)
    definition = Column(Text, nullable=True)
    frequency = Column(Integer, nullable=False, default=1)
    confidence_score = Column(Float, nullable=False, default=0.5)
    centrality_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="concepts")
    outgoing_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.source_concept_id",
        back_populates="source_concept",
        cascade="all, delete-orphan"
    )
    incoming_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.target_concept_id",
        back_populates="target_concept",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_concept_doc_norm", "document_id", "normalized_name"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "name": self.name,
            "normalized_name": self.normalized_name,
            "category": self.category,
            "description": self.description or "",
            "definition": self.definition or "",
            "frequency": self.frequency,
            "confidence_score": round(self.confidence_score, 3),
            "centrality_score": round(self.centrality_score, 3),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
