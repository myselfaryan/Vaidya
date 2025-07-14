"""
Medical documents management endpoints for uploading, processing, and searching medical literature.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.models.schemas import (
    DocumentUpload, DocumentResponse, DocumentSearch,
    PaginatedResponse, PaginationParams
)
from app.models.models import MedicalDocument, DocumentChunk, DocumentType
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from app.dependencies.auth import get_current_user, get_admin_user


router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_data: DocumentUpload = Depends(),
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Upload and process a medical document (admin only).
    
    Args:
        file: Uploaded document file
        document_data: Document metadata
        admin_user: Admin user
        db: Database session
        
    Returns:
        Created document information
    """
    try:
        # Validate file type
        from app.core.config import settings
        
        if not any(file.filename.endswith(ext) for ext in settings.allowed_file_types):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {settings.allowed_file_types}"
            )
        
        # Read file content
        content = await file.read()
        
        # Process based on file type
        if file.filename.endswith('.pdf'):
            text_content = extract_text_from_pdf(content)
        elif file.filename.endswith('.docx'):
            text_content = extract_text_from_docx(content)
        elif file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type"
            )
        
        if not text_content or len(text_content.strip()) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document content is too short or empty"
            )
        
        # Create document record
        document = MedicalDocument(
            title=document_data.title,
            authors=document_data.authors or [],
            source=document_data.source,
            document_type=document_data.document_type,
            content=text_content,
            keywords=document_data.keywords or [],
            word_count=len(text_content.split()),
            processed=False
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document in background
        await process_document_async(document.id, db)
        
        logger.info(f"Document uploaded and queued for processing: {document.id}")
        return DocumentResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.get("/", response_model=PaginatedResponse)
async def get_documents(
    pagination: PaginationParams = Depends(),
    document_type: Optional[DocumentType] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PaginatedResponse:
    """
    Get medical documents with pagination and filtering.
    
    Args:
        pagination: Pagination parameters
        document_type: Optional document type filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Paginated list of documents
    """
    try:
        # Build query
        query = db.query(MedicalDocument)
        
        if document_type:
            query = query.filter(MedicalDocument.document_type == document_type)
        
        # Get total count
        total = query.count()
        
        # Get documents with pagination
        documents = query.offset(
            (pagination.page - 1) * pagination.size
        ).limit(pagination.size).all()
        
        document_responses = [DocumentResponse.from_orm(doc) for doc in documents]
        
        return PaginatedResponse(
            items=document_responses,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
        
    except Exception as e:
        logger.error(f"Failed to get documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Get a specific document by ID.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Document information
    """
    try:
        document = db.query(MedicalDocument).filter(
            MedicalDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.post("/search", response_model=List[DocumentResponse])
async def search_documents(
    search_data: DocumentSearch,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[DocumentResponse]:
    """
    Search medical documents using semantic search.
    
    Args:
        search_data: Search parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of relevant documents
    """
    try:
        # Perform semantic search
        results = vector_service.search_medical_knowledge(
            query=search_data.query,
            document_types=[dt.value for dt in search_data.document_types] if search_data.document_types else None,
            max_results=search_data.limit
        )
        
        # Get document IDs from results
        document_ids = []
        for result in results:
            doc_id = result.get('metadata', {}).get('document_id')
            if doc_id and doc_id not in document_ids:
                document_ids.append(doc_id)
        
        # Fetch documents from database
        documents = db.query(MedicalDocument).filter(
            MedicalDocument.id.in_(document_ids)
        ).all()
        
        # Sort documents by relevance (order of appearance in search results)
        document_dict = {str(doc.id): doc for doc in documents}
        sorted_documents = [document_dict[doc_id] for doc_id in document_ids if doc_id in document_dict]
        
        return [DocumentResponse.from_orm(doc) for doc in sorted_documents]
        
    except Exception as e:
        logger.error(f"Failed to search documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search documents"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a medical document (admin only).
    
    Args:
        document_id: Document ID
        admin_user: Admin user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        document = db.query(MedicalDocument).filter(
            MedicalDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete from vector database
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        if chunks:
            vector_ids = [chunk.vector_id for chunk in chunks if chunk.vector_id]
            if vector_ids:
                vector_service.delete_vectors(vector_ids)
        
        # Delete from database
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        
        db.delete(document)
        db.commit()
        
        logger.info(f"Document deleted: {document_id}")
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: UUID,
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reprocess a document for vector embeddings (admin only).
    
    Args:
        document_id: Document ID
        admin_user: Admin user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        document = db.query(MedicalDocument).filter(
            MedicalDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete existing chunks and vectors
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        if chunks:
            vector_ids = [chunk.vector_id for chunk in chunks if chunk.vector_id]
            if vector_ids:
                vector_service.delete_vectors(vector_ids)
        
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        
        # Mark as unprocessed
        document.processed = False
        db.commit()
        
        # Process document
        await process_document_async(document_id, db)
        
        logger.info(f"Document queued for reprocessing: {document_id}")
        return {"message": "Document queued for reprocessing"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess document"
        )


# Helper functions
def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
        from io import BytesIO
        
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return text
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extract text from PDF"
        )


def extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
        from io import BytesIO
        
        doc = Document(BytesIO(content))
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text
        
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extract text from DOCX"
        )


async def process_document_async(document_id: UUID, db: Session):
    """Process document for vector embeddings."""
    try:
        document = db.query(MedicalDocument).filter(
            MedicalDocument.id == document_id
        ).first()
        
        if not document:
            logger.error(f"Document not found for processing: {document_id}")
            return
        
        # Chunk the document
        chunks = ai_service.chunk_medical_document(document.content)
        
        if not chunks:
            logger.error(f"No chunks created for document: {document_id}")
            return
        
        # Create document metadata
        document_metadata = {
            "title": document.title,
            "document_type": document.document_type.value,
            "source": document.source,
            "authors": document.authors,
            "keywords": document.keywords,
            "publication_date": document.publication_date.isoformat() if document.publication_date else None
        }
        
        # Process chunks for vector storage
        vectors = vector_service.process_document_for_vectors(
            document_id=str(document_id),
            chunks=chunks,
            document_metadata=document_metadata
        )
        
        if not vectors:
            logger.error(f"No vectors created for document: {document_id}")
            return
        
        # Store vectors in Pinecone
        success = vector_service.upsert_vectors(vectors)
        
        if not success:
            logger.error(f"Failed to store vectors for document: {document_id}")
            return
        
        # Create document chunks in database
        for i, chunk in enumerate(chunks):
            chunk_record = DocumentChunk(
                document_id=document_id,
                content=chunk["content"],
                chunk_index=i,
                vector_id=f"{document_id}_{i}",
                start_position=chunk.get("start_position", 0),
                end_position=chunk.get("end_position", 0)
            )
            db.add(chunk_record)
        
        # Mark document as processed
        document.processed = True
        db.commit()
        
        logger.info(f"Document processed successfully: {document_id}")
        
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}")
        db.rollback()


@router.get("/stats/summary")
async def get_document_stats(
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get document collection statistics (admin only).
    
    Args:
        admin_user: Admin user
        db: Database session
        
    Returns:
        Document statistics
    """
    try:
        # Total documents
        total_documents = db.query(MedicalDocument).count()
        
        # Processed documents
        processed_documents = db.query(MedicalDocument).filter(
            MedicalDocument.processed == True
        ).count()
        
        # Documents by type
        document_types = db.query(
            MedicalDocument.document_type,
            db.func.count(MedicalDocument.id)
        ).group_by(MedicalDocument.document_type).all()
        
        # Total chunks
        total_chunks = db.query(DocumentChunk).count()
        
        # Vector database stats
        vector_stats = vector_service.get_index_stats()
        
        return {
            "total_documents": total_documents,
            "processed_documents": processed_documents,
            "processing_rate": processed_documents / total_documents if total_documents > 0 else 0,
            "document_types": {str(doc_type): count for doc_type, count in document_types},
            "total_chunks": total_chunks,
            "vector_database": vector_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document statistics"
        )
