"""
Medical chat endpoints for AI-powered conversations.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.models.schemas import (
    MedicalQuery,
    MedicalResponse,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    MessageFeedback,
    SymptomAnalysis
)
from app.services.ai_service import ai_service
from app.services.conversation_service import conversation_service
from app.dependencies.auth import get_current_user
from app.models.models import User

router = APIRouter()


@router.post("/query", response_model=MedicalResponse)
async def ask_medical_question(
    query: MedicalQuery,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MedicalResponse:
    """
    Ask a medical question and get an AI-generated response.
    
    This endpoint uses RAG (Retrieval-Augmented Generation) to provide
    accurate medical information based on authoritative medical sources.
    """
    try:
        # Get user's medical context
        user_context = {
            "medical_conditions": current_user.medical_conditions or [],
            "medications": current_user.medications or [],
            "allergies": current_user.allergies or []
        }
        
        # Generate AI response
        response = await ai_service.generate_medical_response(
            query=query,
            user_context=user_context
        )
        
        # Save conversation in background if conversation_id provided
        if query.conversation_id:
            background_tasks.add_task(
                conversation_service.add_message_to_conversation,
                db=db,
                conversation_id=query.conversation_id,
                user_id=current_user.id,
                user_message=query.question,
                ai_response=response.answer,
                sources=response.sources,
                medical_entities=response.medical_entities,
                confidence_score=response.confidence
            )
        
        logger.info(f"Medical query processed for user {current_user.id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to process medical query: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process your medical question. Please try again."
        )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """
    Create a new medical conversation.
    """
    try:
        new_conversation = conversation_service.create_conversation(
            db=db,
            user_id=current_user.id,
            conversation_data=conversation
        )
        
        return ConversationResponse.from_orm(new_conversation)
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create conversation"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[ConversationResponse]:
    """
    Get user's conversation history.
    """
    try:
        conversations = conversation_service.get_user_conversations(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        return [ConversationResponse.from_orm(conv) for conv in conversations]
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversations"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """
    Get a specific conversation with messages.
    """
    try:
        conversation = conversation_service.get_conversation_by_id(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        return ConversationResponse.from_orm(conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[MessageResponse]:
    """
    Get messages from a conversation.
    """
    try:
        # Verify conversation ownership
        conversation = conversation_service.get_conversation_by_id(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        messages = conversation_service.get_conversation_messages(
            db=db,
            conversation_id=conversation_id,
            skip=skip,
            limit=limit
        )
        
        return [MessageResponse.from_orm(msg) for msg in messages]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve messages"
        )


@router.post("/messages/{message_id}/feedback")
async def submit_message_feedback(
    message_id: UUID,
    feedback: MessageFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback for a specific message.
    """
    try:
        success = conversation_service.add_message_feedback(
            db=db,
            message_id=message_id,
            user_id=current_user.id,
            rating=feedback.rating,
            feedback_text=feedback.feedback
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Message not found or access denied"
            )
        
        return {"message": "Feedback submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback"
        )


@router.post("/symptoms/analyze", response_model=SymptomAnalysis)
async def analyze_symptoms(
    symptoms: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SymptomAnalysis:
    """
    Analyze a list of symptoms and provide medical insights.
    
    This endpoint provides educational information about possible conditions
    based on reported symptoms. It should not be used for medical diagnosis.
    """
    try:
        if not symptoms:
            raise HTTPException(
                status_code=400,
                detail="At least one symptom must be provided"
            )
        
        # Get user's medical context
        user_context = {
            "medical_conditions": current_user.medical_conditions or [],
            "medications": current_user.medications or [],
            "allergies": current_user.allergies or []
        }
        
        # Analyze symptoms using AI service
        analysis = await ai_service.analyze_symptoms(
            symptoms=symptoms,
            user_context=user_context
        )
        
        # Convert to response format
        return SymptomAnalysis(
            symptoms=analysis["symptoms"],
            possible_conditions=analysis.get("possible_conditions", []),
            recommendations=analysis.get("recommendations", []),
            urgency_level=analysis.get("urgency_level", "medium"),
            disclaimer=analysis["disclaimer"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze symptoms: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze symptoms"
        )


@router.get("/emergency")
async def get_emergency_info():
    """
    Get emergency contact information and red flag symptoms.
    """
    return {
        "emergency_contacts": {
            "us": "911",
            "uk": "999", 
            "eu": "112",
            "poison_control_us": "1-800-222-1222"
        },
        "red_flag_symptoms": [
            "Severe chest pain or pressure",
            "Difficulty breathing or shortness of breath",
            "Signs of stroke (face drooping, arm weakness, speech difficulty)",
            "Severe allergic reaction (anaphylaxis)",
            "Severe bleeding that won't stop",
            "Severe abdominal pain",
            "High fever with neck stiffness",
            "Loss of consciousness",
            "Severe burns",
            "Thoughts of self-harm or suicide"
        ],
        "when_to_seek_immediate_care": [
            "Any life-threatening symptoms",
            "Severe pain that isn't improving",
            "High fever in infants under 3 months",
            "Severe dehydration",
            "Severe mental health crisis"
        ],
        "disclaimer": "If you are experiencing a medical emergency, call emergency services immediately. Do not rely on this AI system for emergency medical advice."
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation (soft delete for compliance).
    """
    try:
        success = conversation_service.delete_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete conversation"
        )
