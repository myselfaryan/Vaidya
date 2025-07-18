"""
Document-related Pydantic models for request/response validation.
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator
from app.models.models import DocumentType, DocumentStatus

class DocumentBase(BaseModel):
    """Base document model with common fields."""
    title: str = Field(..., max_length=255, description="Title of the document")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the document")
    document_type: DocumentType = Field(..., description="Type of the document")
    source: str = Field("web", description="Source of the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class DocumentCreate(DocumentBase):
    """Model for creating a new document."""
    content: str = Field(..., description="Content of the document")

class DocumentUpdate(BaseModel):
    """Model for updating an existing document."""
    title: Optional[str] = Field(None, max_length=255, description="Title of the document")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the document")
    document_type: Optional[DocumentType] = Field(None, description="Type of the document")
    status: Optional[DocumentStatus] = Field(None, description="Status of the document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class DocumentResponse(DocumentBase):
    """Document response model with read-only fields."""
    id: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    uploaded_by: str
    
    class Config:
        orm_mode = True

class DocumentSearch(BaseModel):
    """Model for document search parameters."""
    query: Optional[str] = Field(None, description="Search query string")
    document_type: Optional[DocumentType] = Field(None, description="Filter by document type")
    status: Optional[DocumentStatus] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    sort_by: str = Field("updated_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

class DocumentBatchUpload(BaseModel):
    """Model for batch document uploads."""
    document_type: DocumentType
    source: str = "batch-upload"
    metadata: Dict[str, Any] = {}

class DocumentStatistics(BaseModel):
    """Model for document statistics."""
    total_documents: int
    documents_by_type: List[Dict[str, Union[str, int]]]
    documents_by_status: List[Dict[str, Union[str, int]]]
    storage_usage: Dict[str, Union[int, float]]
    recent_activity: List[Dict[str, Any]]

class DocumentSearchResult(BaseModel):
    """Model for document search results with relevance scores."""
    document: DocumentResponse
    score: Optional[float] = None
    highlights: Optional[Dict[str, List[str]]] = None

class DocumentBatchStatus(BaseModel):
    """Model for batch document processing status."""
    batch_id: str
    total_documents: int
    processed_documents: int
    failed_documents: int
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    errors: Optional[List[Dict[str, Any]]] = None

class DocumentChunkResponse(BaseModel):
    """Model for document chunk response."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class DocumentProcessRequest(BaseModel):
    """Model for document processing request."""
    reprocess: bool = Field(False, description="Whether to reprocess the document if already processed")
    update_vectors: bool = Field(True, description="Whether to update vector embeddings")
    chunk_size: Optional[int] = Field(None, description="Custom chunk size")
    chunk_overlap: Optional[int] = Field(None, description="Custom chunk overlap")

class DocumentProcessResponse(BaseModel):
    """Model for document processing response."""
    document_id: str
    status: str
    chunks_processed: int
    vectors_updated: int
    processing_time: float
    error: Optional[str] = None
