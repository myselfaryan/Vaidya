"""
SQLAlchemy models for the Vaidya medical chatbot system.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, 
    String, Text, JSON, Float, LargeBinary
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class UserRole(PyEnum):
    """User role enumeration."""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class ConversationStatus(PyEnum):
    """Conversation status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageType(PyEnum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    SYSTEM = "system"


class DocumentType(PyEnum):
    """Document type enumeration."""
    MEDICAL_GUIDELINE = "medical_guideline"
    DRUG_INFO = "drug_info"
    RESEARCH_PAPER = "research_paper"
    CLINICAL_TRIAL = "clinical_trial"
    TEXTBOOK = "textbook"


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number = Column(String(20))
    date_of_birth = Column(DateTime)
    
    # Medical information (encrypted)
    medical_conditions = Column(Text)  # JSON encrypted
    medications = Column(Text)  # JSON encrypted
    allergies = Column(Text)  # JSON encrypted
    
    # Account settings
    role = Column(Enum(UserRole), default=UserRole.PATIENT)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Privacy settings
    data_sharing_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Conversation(Base):
    """Conversation model for chat sessions."""
    
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255))
    summary = Column(Text)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    
    # Medical context
    primary_concern = Column(String(500))
    symptoms = Column(JSON)  # List of symptoms
    medical_context = Column(JSON)  # Additional context
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Message model for individual chat messages."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    is_from_user = Column(Boolean, nullable=False)
    
    # AI processing metadata
    tokens_used = Column(Integer)
    processing_time = Column(Float)
    confidence_score = Column(Float)
    
    # Retrieved context
    retrieved_sources = Column(JSON)  # List of source document IDs
    medical_entities = Column(JSON)  # Extracted medical entities
    
    # Feedback
    user_rating = Column(Integer)  # 1-5 rating
    user_feedback = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class MedicalDocument(Base):
    """Medical document model for knowledge base."""
    
    __tablename__ = "medical_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    title = Column(String(500), nullable=False)
    authors = Column(JSON)  # List of authors
    source = Column(String(255))  # Journal, publisher, etc.
    document_type = Column(Enum(DocumentType), nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    abstract = Column(Text)
    keywords = Column(JSON)  # List of keywords
    
    # Metadata
    publication_date = Column(DateTime)
    language = Column(String(10), default="en")
    doi = Column(String(255))
    url = Column(String(500))
    
    # Processing metadata
    word_count = Column(Integer)
    processed = Column(Boolean, default=False)
    embedding_model = Column(String(100))
    
    # Quality metrics
    reliability_score = Column(Float)  # 0-1 score
    medical_accuracy_score = Column(Float)  # 0-1 score
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    """Document chunk model for vector embeddings."""
    
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("medical_documents.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Vector storage reference
    vector_id = Column(String(255))  # Pinecone vector ID
    
    # Metadata
    start_position = Column(Integer)
    end_position = Column(Integer)
    medical_entities = Column(JSON)  # Extracted medical entities
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("MedicalDocument", back_populates="chunks")


class AuditLog(Base):
    """Audit log for security and compliance tracking."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    action = Column(String(100), nullable=False)
    resource = Column(String(100))
    resource_id = Column(String(255))
    
    # Request details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    endpoint = Column(String(255))
    method = Column(String(10))
    
    # Response details
    status_code = Column(Integer)
    response_time = Column(Float)
    
    # Additional context
    metadata = Column(JSON)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class SystemMetrics(Base):
    """System metrics for monitoring and analytics."""
    
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    
    # Tags for grouping
    tags = Column(JSON)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class UserSession(Base):
    """User session tracking for security."""
    
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True)
    
    # Session details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    device_info = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
