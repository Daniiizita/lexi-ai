from sqlalchemy import Column, String, Integer, Float, Text, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()


class TranslationJob(Base):
    __tablename__ = "translation_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    source_lang = Column(String(10), default="en")
    target_lang = Column(String(10), default="pt-BR")
    
    # Storage paths
    source_path = Column(Text)
    translated_path = Column(Text)
    
    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    error_message = Column(Text)
    
    # Métricas
    total_chunks = Column(Integer)
    chunks_translated = Column(Integer, default=0)
    model_name = Column(String(100))
    translation_time_seconds = Column(Float)
    
    # Auditoria
    user_id = Column(String(100))
    ip_address = Column(INET)
    
    # Relacionamento
    chunks = relationship("TranslationChunk", back_populates="job", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "filename": self.filename,
            "status": self.status,
            "progress": f"{self.chunks_translated}/{self.total_chunks}" if self.total_chunks else "0/0",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "translation_time": self.translation_time_seconds
        }


class TranslationChunk(Base):
    __tablename__ = "translation_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("translation_jobs.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text)
    
    status = Column(String(50), default="pending", index=True)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    
    # Metadata LEXI
    decisions = Column(JSONB)
    terms_used = Column(JSONB)
    flags = Column(JSONB)
    
    # Relacionamento
    job = relationship("TranslationJob", back_populates="chunks")