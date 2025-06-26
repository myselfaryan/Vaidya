"""
AI service for medical chatbot responses using OpenAI and RAG architecture.
"""

import time
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from loguru import logger

from ..core.config import settings
from ..models.schemas import MedicalQuery, MedicalResponse
from .vector_service import vector_service


class AIService:
    """Service for AI-powered medical responses using RAG architecture."""
    
    def __init__(self):
        """Initialize the AI service."""
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.max_chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup prompt templates for different medical scenarios."""
        
        self.medical_prompt = PromptTemplate(
            input_variables=["question", "context", "medical_history"],
            template="""You are Vaidya, an AI medical assistant designed to provide accurate, helpful, and empathetic medical information. You have access to authoritative medical literature and guidelines.

MEDICAL CONTEXT:
{context}

USER'S MEDICAL HISTORY:
{medical_history}

USER'S QUESTION:
{question}

INSTRUCTIONS:
1. Provide accurate, evidence-based medical information
2. Use the provided context from medical literature
3. Consider the user's medical history if relevant
4. Be empathetic and supportive
5. Always include appropriate medical disclaimers
6. Suggest when to seek professional medical care
7. Provide clear, understandable explanations
8. Include relevant follow-up questions when appropriate

RESPONSE FORMAT:
- Answer the user's question directly and clearly
- Reference specific medical sources when applicable
- Include confidence level in your response
- Suggest follow-up questions or next steps
- End with an appropriate medical disclaimer

IMPORTANT: This is for educational purposes only. Always recommend consulting with healthcare professionals for medical decisions.

Response:"""
        )
        
        self.symptom_analysis_prompt = PromptTemplate(
            input_variables=["symptoms", "context", "medical_history"],
            template="""You are analyzing symptoms to provide educational information about possible conditions.

SYMPTOMS REPORTED:
{symptoms}

MEDICAL LITERATURE CONTEXT:
{context}

USER'S MEDICAL HISTORY:
{medical_history}

Provide a structured analysis including:
1. Possible conditions (with confidence levels)
2. Recommended actions
3. Urgency level (low/medium/high/emergency)
4. When to seek immediate care
5. General health recommendations

Remember: This is educational information only, not a medical diagnosis."""
        )
        
        self.drug_interaction_prompt = PromptTemplate(
            input_variables=["medications", "context"],
            template="""Analyze potential drug interactions and provide safety information.

MEDICATIONS:
{medications}

DRUG INTERACTION DATABASE:
{context}

Provide:
1. Potential interactions
2. Severity levels
3. Recommendations
4. Monitoring requirements
5. When to consult pharmacist/doctor

Include appropriate safety disclaimers."""
        )
    
    async def generate_medical_response(
        self,
        query: MedicalQuery,
        user_context: Optional[Dict[str, Any]] = None
    ) -> MedicalResponse:
        """
        Generate a medical response using RAG architecture.
        
        Args:
            query: Medical query object
            user_context: Optional user medical context
            
        Returns:
            Medical response with sources and confidence
        """
        start_time = time.time()
        
        try:
            # Step 1: Retrieve relevant medical information
            retrieved_docs = await self._retrieve_medical_context(query.question)
            
            # Step 2: Prepare context and medical history
            context = self._format_retrieved_context(retrieved_docs)
            medical_history = self._format_medical_history(user_context)
            
            # Step 3: Generate response using LLM
            response_content = await self._generate_llm_response(
                query.question,
                context,
                medical_history
            )
            
            # Step 4: Extract medical entities
            medical_entities = await self._extract_medical_entities(query.question)
            
            # Step 5: Generate follow-up questions
            follow_up_questions = await self._generate_follow_up_questions(
                query.question,
                response_content
            )
            
            # Step 6: Calculate confidence score
            confidence = self._calculate_confidence_score(retrieved_docs, response_content)
            
            processing_time = time.time() - start_time
            
            # Log the interaction
            logger.info(f"Generated medical response in {processing_time:.2f}s with confidence {confidence:.2f}")
            
            return MedicalResponse(
                answer=response_content,
                confidence=confidence,
                sources=[doc["metadata"] for doc in retrieved_docs],
                medical_entities=medical_entities,
                disclaimer=settings.medical_disclaimer,
                follow_up_questions=follow_up_questions
            )
            
        except Exception as e:
            logger.error(f"Failed to generate medical response: {e}")
            
            # Return safe fallback response
            return MedicalResponse(
                answer="I apologize, but I'm unable to process your medical question at the moment. Please consult with a healthcare professional for medical advice.",
                confidence=0.0,
                sources=[],
                medical_entities=[],
                disclaimer=settings.medical_disclaimer,
                follow_up_questions=[]
            )
    
    async def _retrieve_medical_context(self, question: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant medical context from the knowledge base.
        
        Args:
            question: User's medical question
            
        Returns:
            List of relevant medical documents
        """
        try:
            # Search the vector database for relevant medical information
            results = vector_service.search_medical_knowledge(
                query=question,
                max_results=settings.max_retrieval_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve medical context: {e}")
            return []
    
    def _format_retrieved_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context string.
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "No specific medical literature found for this query."
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            source_info = f"Source {i}: {doc.get('title', 'Unknown')}"
            if doc.get('source'):
                source_info += f" ({doc['source']})"
            
            context_part = f"{source_info}\nContent: {doc.get('content', '')}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _format_medical_history(self, user_context: Optional[Dict[str, Any]]) -> str:
        """
        Format user's medical history for context.
        
        Args:
            user_context: User's medical context
            
        Returns:
            Formatted medical history string
        """
        if not user_context:
            return "No medical history provided."
        
        history_parts = []
        
        if user_context.get("medical_conditions"):
            conditions = ", ".join(user_context["medical_conditions"])
            history_parts.append(f"Medical conditions: {conditions}")
        
        if user_context.get("medications"):
            medications = ", ".join(user_context["medications"])
            history_parts.append(f"Current medications: {medications}")
        
        if user_context.get("allergies"):
            allergies = ", ".join(user_context["allergies"])
            history_parts.append(f"Known allergies: {allergies}")
        
        return "\n".join(history_parts) if history_parts else "No medical history provided."
    
    async def _generate_llm_response(
        self,
        question: str,
        context: str,
        medical_history: str
    ) -> str:
        """
        Generate response using OpenAI LLM.
        
        Args:
            question: User's question
            context: Retrieved medical context
            medical_history: User's medical history
            
        Returns:
            Generated response
        """
        try:
            # Format the prompt
            prompt = self.medical_prompt.format(
                question=question,
                context=context,
                medical_history=medical_history
            )
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are Vaidya, a knowledgeable and empathetic AI medical assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent medical advice
                max_tokens=1000,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            raise
    
    async def _extract_medical_entities(self, text: str) -> List[str]:
        """
        Extract medical entities from text using OpenAI.
        
        Args:
            text: Input text
            
        Returns:
            List of medical entities
        """
        try:
            prompt = f"""Extract medical entities (symptoms, conditions, medications, anatomy) from this text:
            
"{text}"

Return only the medical terms as a comma-separated list, or "None" if no medical entities found."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical entity extraction system. Extract only medical terms."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            entities_text = response.choices[0].message.content.strip()
            
            if entities_text.lower() == "none":
                return []
            
            entities = [entity.strip() for entity in entities_text.split(",")]
            return [entity for entity in entities if entity]
            
        except Exception as e:
            logger.error(f"Failed to extract medical entities: {e}")
            return []
    
    async def _generate_follow_up_questions(
        self,
        original_question: str,
        response: str
    ) -> List[str]:
        """
        Generate relevant follow-up questions.
        
        Args:
            original_question: Original user question
            response: Generated response
            
        Returns:
            List of follow-up questions
        """
        try:
            prompt = f"""Based on this medical question and answer, suggest 3 relevant follow-up questions:

Question: {original_question}
Answer: {response}

Generate questions that would help the user understand their condition better or provide more specific guidance."""
            
            response_obj = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Generate helpful medical follow-up questions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=300
            )
            
            questions_text = response_obj.choices[0].message.content.strip()
            questions = [q.strip() for q in questions_text.split("\n") if q.strip()]
            
            # Clean up questions (remove numbering, etc.)
            cleaned_questions = []
            for q in questions:
                q = q.strip("1234567890.- ")
                if q and "?" in q:
                    cleaned_questions.append(q)
            
            return cleaned_questions[:3]  # Return max 3 questions
            
        except Exception as e:
            logger.error(f"Failed to generate follow-up questions: {e}")
            return []
    
    def _calculate_confidence_score(
        self,
        retrieved_docs: List[Dict[str, Any]],
        response: str
    ) -> float:
        """
        Calculate confidence score based on retrieval quality and response.
        
        Args:
            retrieved_docs: Retrieved documents
            response: Generated response
            
        Returns:
            Confidence score between 0 and 1
        """
        try:
            # Base confidence from retrieval quality
            if not retrieved_docs:
                base_confidence = 0.2
            else:
                # Average similarity scores from vector search
                avg_similarity = sum(doc.get("score", 0) for doc in retrieved_docs) / len(retrieved_docs)
                base_confidence = min(avg_similarity, 0.9)
            
            # Adjust based on response characteristics
            response_length = len(response.split())
            if response_length < 50:
                length_factor = 0.8  # Very short responses get lower confidence
            elif response_length > 300:
                length_factor = 0.9  # Very long responses might be less focused
            else:
                length_factor = 1.0
            
            # Check for disclaimer presence
            disclaimer_factor = 1.0 if "consult" in response.lower() else 0.95
            
            # Final confidence calculation
            confidence = base_confidence * length_factor * disclaimer_factor
            
            return max(0.1, min(0.95, confidence))  # Clamp between 0.1 and 0.95
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence score: {e}")
            return 0.5
    
    async def analyze_symptoms(
        self,
        symptoms: List[str],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze symptoms and provide structured medical information.
        
        Args:
            symptoms: List of symptoms
            user_context: Optional user medical context
            
        Returns:
            Structured symptom analysis
        """
        try:
            # Retrieve relevant medical information for symptoms
            symptom_query = f"symptoms: {', '.join(symptoms)}"
            retrieved_docs = await self._retrieve_medical_context(symptom_query)
            
            context = self._format_retrieved_context(retrieved_docs)
            medical_history = self._format_medical_history(user_context)
            
            # Generate symptom analysis
            prompt = self.symptom_analysis_prompt.format(
                symptoms=", ".join(symptoms),
                context=context,
                medical_history=medical_history
            )
            
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical AI providing symptom analysis for educational purposes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            return {
                "symptoms": symptoms,
                "analysis": analysis_text,
                "sources": [doc["metadata"] for doc in retrieved_docs],
                "confidence": self._calculate_confidence_score(retrieved_docs, analysis_text),
                "disclaimer": settings.medical_disclaimer
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze symptoms: {e}")
            return {
                "symptoms": symptoms,
                "analysis": "I'm unable to analyze these symptoms at the moment. Please consult with a healthcare professional.",
                "sources": [],
                "confidence": 0.0,
                "disclaimer": settings.medical_disclaimer
            }
    
    def chunk_medical_document(self, content: str) -> List[Dict[str, Any]]:
        """
        Chunk medical document content for vector storage.
        
        Args:
            content: Document content
            
        Returns:
            List of document chunks
        """
        try:
            # Split the content into chunks
            chunks = self.text_splitter.split_text(content)
            
            # Create chunk objects with metadata
            chunk_objects = []
            current_position = 0
            
            for i, chunk in enumerate(chunks):
                start_pos = content.find(chunk, current_position)
                end_pos = start_pos + len(chunk)
                
                chunk_obj = {
                    "content": chunk,
                    "chunk_index": i,
                    "start_position": start_pos,
                    "end_position": end_pos
                }
                chunk_objects.append(chunk_obj)
                current_position = end_pos
            
            logger.info(f"Created {len(chunk_objects)} chunks from document")
            return chunk_objects
            
        except Exception as e:
            logger.error(f"Failed to chunk document: {e}")
            return []


# Global AI service instance
ai_service = AIService()
