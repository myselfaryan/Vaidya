"""
Pydantic schemas for API request and response validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from .models import UserRole, ConversationStatus, MessageType, DocumentType


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        use_enum_values = True


# User schemas
class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8)
    phone_number: Optional[str] = None
    data_sharing_consent: bool = False
    marketing_consent: bool = False


class UserUpdate(BaseSchema):
    """Schema for user updates."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    data_sharing_consent: Optional[bool] = None
    marketing_consent: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserProfile(UserResponse):
    """Extended user profile schema."""
    medical_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None


# Authentication schemas
class LoginRequest(BaseSchema):
    """Schema for login request."""
    username: str
    password: str


class TokenResponse(BaseSchema):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordReset(BaseSchema):
    """Schema for password reset."""
    email: EmailStr


class PasswordChange(BaseSchema):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8)


# Conversation schemas
class ConversationCreate(BaseSchema):
    """Schema for conversation creation."""
    title: Optional[str] = None
    primary_concern: Optional[str] = None
    symptoms: Optional[List[str]] = None


class ConversationUpdate(BaseSchema):
    """Schema for conversation updates."""
    title: Optional[str] = None
    status: Optional[ConversationStatus] = None


class ConversationResponse(BaseSchema):
    """Schema for conversation response."""
    id: UUID
    title: Optional[str] = None
    summary: Optional[str] = None
    status: ConversationStatus
    primary_concern: Optional[str] = None
    symptoms: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0


# Message schemas
class MessageCreate(BaseSchema):
    """Schema for message creation."""
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: MessageType = MessageType.TEXT


class MessageResponse(BaseSchema):
    """Schema for message response."""
    id: UUID
    content: str
    message_type: MessageType
    is_from_user: bool
    confidence_score: Optional[float] = None
    retrieved_sources: Optional[List[Dict[str, Any]]] = None
    medical_entities: Optional[List[str]] = None
    created_at: datetime


class MessageFeedback(BaseSchema):
    """Schema for message feedback."""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


# Medical query schemas
class MedicalQuery(BaseSchema):
    """Schema for medical queries."""
    question: str = Field(..., min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[UUID] = None


class MedicalResponse(BaseSchema):
    """Schema for medical responses."""
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: List[Dict[str, Any]] = []
    medical_entities: List[str] = []
    disclaimer: str
    follow_up_questions: Optional[List[str]] = None


# Document schemas
class DocumentUpload(BaseSchema):
    """Schema for document upload."""
    title: str = Field(..., min_length=1, max_length=500)
    document_type: DocumentType
    authors: Optional[List[str]] = None
    source: Optional[str] = None
    keywords: Optional[List[str]] = None


class DocumentResponse(BaseSchema):
    """Schema for document response."""
    id: UUID
    title: str
    authors: Optional[List[str]] = None
    source: Optional[str] = None
    document_type: DocumentType
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    word_count: Optional[int] = None
    processed: bool
    reliability_score: Optional[float] = None
    created_at: datetime


class DocumentSearch(BaseSchema):
    """Schema for document search."""
    query: str = Field(..., min_length=1, max_length=500)
    document_types: Optional[List[DocumentType]] = None
    limit: int = Field(default=10, ge=1, le=50)


# Health check schemas
class HealthCheck(BaseSchema):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]


# Analytics schemas
class UsageStats(BaseSchema):
    """Schema for usage statistics."""
    total_users: int
    active_conversations: int
    messages_today: int
    avg_response_time: float
    system_health: str


class UserActivity(BaseSchema):
    """Schema for user activity."""
    user_id: UUID
    conversations_count: int
    messages_count: int
    last_active: datetime
    avg_session_duration: float


# WebSocket schemas
class WebSocketMessage(BaseSchema):
    """Schema for WebSocket messages."""
    type: str = Field(..., regex="^(message|typing|system)$")
    content: Optional[str] = None
    conversation_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TypingIndicator(BaseSchema):
    """Schema for typing indicator."""
    conversation_id: UUID
    is_typing: bool
    user_id: UUID


# Error schemas
class ErrorResponse(BaseSchema):
    """Schema for error responses."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationError(BaseSchema):
    """Schema for validation errors."""
    field: str
    message: str
    invalid_value: Optional[Any] = None


# Pagination schemas
class PaginationParams(BaseSchema):
    """Schema for pagination parameters."""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseSchema):
    """Schema for paginated responses."""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    
    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        total = values.get('total', 0)
        size = values.get('size', 20)
        return (total + size - 1) // size if total > 0 else 0


# Medical entity schemas
class MedicalEntity(BaseSchema):
    """Schema for medical entities."""
    text: str
    label: str
    confidence: float
    start: int
    end: int


class SymptomAnalysis(BaseSchema):
    """Schema for symptom analysis."""
    symptoms: List[str]
    possible_conditions: List[Dict[str, Any]]
    recommendations: List[str]
    urgency_level: str = Field(..., regex="^(low|medium|high|emergency)$")
    disclaimer: str


# Integration schemas
class EHRIntegration(BaseSchema):
    """Schema for EHR integration."""
    patient_id: str
    ehr_system: str
    data_mapping: Dict[str, str]
    sync_status: str


class TelehealthSession(BaseSchema):
    """Schema for telehealth sessions."""
    session_id: UUID
    provider_id: UUID
    patient_id: UUID
    scheduled_time: datetime
    duration_minutes: int
    status: str
    notes: Optional[str] = None
