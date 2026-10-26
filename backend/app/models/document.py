import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from ..database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    storage_path = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, default="uploaded")
    error_message = Column(Text, nullable=True)
    warning_message = Column(Text, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_date = Column(DateTime, nullable=True)
    
    total_chunks = Column(Integer, default=0)
    total_terms = Column(Integer, default=0)
    total_concepts = Column(Integer, default=0)
    total_relationships = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)

    # Cascading relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_index")
    terminologies = relationship("Terminology", back_populates="document", cascade="all, delete-orphan", order_by="desc(Terminology.frequency)")
    concepts = relationship("Concept", back_populates="document", cascade="all, delete-orphan", order_by="desc(Concept.confidence_score)")
    relationships = relationship("Relationship", back_populates="document", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan", order_by="desc(ProcessingJob.created_at)")

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "status": self.status,
            "error_message": self.error_message,
            "warning_message": self.warning_message,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "processed_date": self.processed_date.isoformat() if self.processed_date else None,
            "total_chunks": self.total_chunks,
            "total_terms": self.total_terms,
            "total_concepts": self.total_concepts,
            "total_relationships": self.total_relationships,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
        }
