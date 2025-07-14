"""
Conversation service for managing medical chat conversations and messages.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

from ..models.models import Conversation, Message, User, ConversationStatus, MessageType
from ..models.schemas import ConversationCreate, ConversationUpdate, MessageCreate


class ConversationService:
    """Service for managing conversations and messages."""
    
    def create_conversation(
        self,
        db: Session,
        user_id: UUID,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            db: Database session
            user_id: User ID
            conversation_data: Conversation creation data
            
        Returns:
            Created conversation object
        """
        try:
            # Generate title if not provided
            title = conversation_data.title
            if not title and conversation_data.primary_concern:
                title = conversation_data.primary_concern[:100]
            elif not title:
                title = f"Medical Consultation - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            
            conversation = Conversation(
                user_id=user_id,
                title=title,
                primary_concern=conversation_data.primary_concern,
                symptoms=conversation_data.symptoms or [],
                medical_context={}
            )
            
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"Created conversation {conversation.id} for user {user_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            db.rollback()
            raise
    
    def get_conversation_by_id(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: UUID
    ) -> Optional[Conversation]:
        """
        Get conversation by ID with user verification.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID for verification
            
        Returns:
            Conversation object if found and belongs to user, None otherwise
        """
        return db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.status != ConversationStatus.DELETED
        ).first()
    
    def get_user_conversations(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Get user's conversations with pagination.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of conversations to skip
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        return db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status != ConversationStatus.DELETED
        ).order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
    
    def update_conversation(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: UUID,
        update_data: ConversationUpdate
    ) -> Optional[Conversation]:
        """
        Update conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID for verification
            update_data: Update data
            
        Returns:
            Updated conversation object if successful, None otherwise
        """
        conversation = self.get_conversation_by_id(db, conversation_id, user_id)
        
        if not conversation:
            return None
        
        try:
            if update_data.title is not None:
                conversation.title = update_data.title
            
            if update_data.status is not None:
                conversation.status = update_data.status
            
            conversation.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"Updated conversation {conversation_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to update conversation {conversation_id}: {e}")
            db.rollback()
            return None
    
    def delete_conversation(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Soft delete a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID for verification
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation_by_id(db, conversation_id, user_id)
        
        if not conversation:
            return False
        
        try:
            conversation.status = ConversationStatus.DELETED
            conversation.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Deleted conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            db.rollback()
            return False
    
    def add_message_to_conversation(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: UUID,
        user_message: str,
        ai_response: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        medical_entities: Optional[List[str]] = None,
        confidence_score: Optional[float] = None
    ) -> bool:
        """
        Add user message and AI response to conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID
            user_message: User's message content
            ai_response: AI's response content
            sources: Retrieved sources for the response
            medical_entities: Extracted medical entities
            confidence_score: AI confidence score
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation_by_id(db, conversation_id, user_id)
        
        if not conversation:
            return False
        
        try:
            # Add user message
            user_msg = Message(
                conversation_id=conversation_id,
                content=user_message,
                message_type=MessageType.TEXT,
                is_from_user=True
            )
            db.add(user_msg)
            
            # Add AI response
            ai_msg = Message(
                conversation_id=conversation_id,
                content=ai_response,
                message_type=MessageType.TEXT,
                is_from_user=False,
                confidence_score=confidence_score,
                retrieved_sources=sources or [],
                medical_entities=medical_entities or []
            )
            db.add(ai_msg)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Added messages to conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add messages to conversation {conversation_id}: {e}")
            db.rollback()
            return False
    
    def get_conversation_messages(
        self,
        db: Session,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """
        Get messages from a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            skip: Number of messages to skip
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).offset(skip).limit(limit).all()
    
    def get_message_by_id(
        self,
        db: Session,
        message_id: UUID,
        user_id: UUID
    ) -> Optional[Message]:
        """
        Get message by ID with user verification.
        
        Args:
            db: Database session
            message_id: Message ID
            user_id: User ID for verification
            
        Returns:
            Message object if found and user has access, None otherwise
        """
        return db.query(Message).join(Conversation).filter(
            Message.id == message_id,
            Conversation.user_id == user_id
        ).first()
    
    def add_message_feedback(
        self,
        db: Session,
        message_id: UUID,
        user_id: UUID,
        rating: int,
        feedback_text: Optional[str] = None
    ) -> bool:
        """
        Add feedback to a message.
        
        Args:
            db: Database session
            message_id: Message ID
            user_id: User ID for verification
            rating: Rating (1-5)
            feedback_text: Optional feedback text
            
        Returns:
            True if successful, False otherwise
        """
        message = self.get_message_by_id(db, message_id, user_id)
        
        if not message or message.is_from_user:
            return False
        
        try:
            message.user_rating = rating
            message.user_feedback = feedback_text
            
            db.commit()
            
            logger.info(f"Added feedback to message {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add feedback to message {message_id}: {e}")
            db.rollback()
            return False
    
    def get_conversation_summary(
        self,
        db: Session,
        conversation_id: UUID,
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation summary with statistics.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID for verification
            
        Returns:
            Conversation summary with statistics
        """
        conversation = self.get_conversation_by_id(db, conversation_id, user_id)
        
        if not conversation:
            return None
        
        # Get message count
        message_count = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).count()
        
        # Get average AI confidence
        avg_confidence = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_from_user == False,
            Message.confidence_score.isnot(None)
        ).with_entities(Message.confidence_score).all()
        
        if avg_confidence:
            avg_confidence_score = sum(score[0] for score in avg_confidence) / len(avg_confidence)
        else:
            avg_confidence_score = None
        
        return {
            "conversation_id": conversation_id,
            "title": conversation.title,
            "primary_concern": conversation.primary_concern,
            "symptoms": conversation.symptoms,
            "status": conversation.status,
            "message_count": message_count,
            "avg_confidence": avg_confidence_score,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at
        }
    
    def search_conversations(
        self,
        db: Session,
        user_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Conversation]:
        """
        Search user's conversations by title or content.
        
        Args:
            db: Database session
            user_id: User ID
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching conversations
        """
        return db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status != ConversationStatus.DELETED,
            Conversation.title.ilike(f"%{query}%")
        ).order_by(desc(Conversation.updated_at)).limit(limit).all()
    
    def get_user_conversation_stats(
        self,
        db: Session,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get user's conversation statistics.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with conversation statistics
        """
        # Total conversations
        total_conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status != ConversationStatus.DELETED
        ).count()
        
        # Active conversations
        active_conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status == ConversationStatus.ACTIVE
        ).count()
        
        # Total messages
        total_messages = db.query(Message).join(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status != ConversationStatus.DELETED
        ).count()
        
        # Average messages per conversation
        avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0
        
        return {
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": round(avg_messages_per_conversation, 2)
        }


# Global conversation service instance
conversation_service = ConversationService()
