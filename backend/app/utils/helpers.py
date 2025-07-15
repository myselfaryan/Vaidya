"""
Utility functions for the Vaidya medical chatbot backend.
This module provides common helper functions for data processing,
validation, and medical-specific operations.
"""

import re
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from email.utils import parseaddr
from loguru import logger
import bleach


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        text: Raw user input text
        
    Returns:
        Sanitized text safe for processing
    """
    if not text:
        return ""
    
    # Remove HTML tags and dangerous characters
    sanitized = bleach.clean(text, tags=[], attributes={}, strip=True)
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
    return sanitized.strip()


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    if not email:
        return False
    
    # Parse email address
    parsed = parseaddr(email)
    if not parsed[1]:
        return False
    
    # Basic email regex validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, parsed[1]))


def validate_medical_input(symptoms: str) -> Dict[str, Any]:
    """
    Validate and analyze medical symptom input.
    
    Args:
        symptoms: User-reported symptoms
        
    Returns:
        Validation result with analysis
    """
    if not symptoms:
        return {"valid": False, "error": "Symptoms cannot be empty"}
    
    # Sanitize input
    clean_symptoms = sanitize_input(symptoms)
    
    # Check for emergency keywords
    emergency_keywords = [
        "chest pain", "heart attack", "stroke", "unconscious", "bleeding",
        "choking", "severe pain", "can't breathe", "suicide", "overdose"
    ]
    
    has_emergency = any(keyword in clean_symptoms.lower() for keyword in emergency_keywords)
    
    # Check for minimum length
    if len(clean_symptoms) < 10:
        return {"valid": False, "error": "Please provide more detailed symptoms"}
    
    return {
        "valid": True,
        "symptoms": clean_symptoms,
        "emergency_detected": has_emergency,
        "word_count": len(clean_symptoms.split())
    }


def generate_session_id() -> str:
    """
    Generate a secure session ID.
    
    Returns:
        Cryptographically secure session ID
    """
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def format_medical_response(response: str) -> str:
    """
    Format AI response for medical context with appropriate disclaimers.
    
    Args:
        response: Raw AI response
        
    Returns:
        Formatted response with medical disclaimers
    """
    if not response:
        return ""
    
    # Add medical disclaimer
    disclaimer = (
        "\n\n⚠️ **Medical Disclaimer**: This information is for educational purposes only "
        "and should not replace professional medical advice. Please consult a healthcare "
        "provider for proper diagnosis and treatment."
    )
    
    # Format response with proper line breaks
    formatted = response.strip() + disclaimer
    
    return formatted


def extract_urgency_level(symptoms: str) -> str:
    """
    Determine urgency level based on symptoms.
    
    Args:
        symptoms: User-reported symptoms
        
    Returns:
        Urgency level (low, medium, high, emergency)
    """
    if not symptoms:
        return "low"
    
    symptoms_lower = symptoms.lower()
    
    # Emergency level symptoms
    emergency_indicators = [
        "chest pain", "heart attack", "stroke", "unconscious", "severe bleeding",
        "can't breathe", "choking", "severe allergic reaction", "overdose"
    ]
    
    # High urgency symptoms
    high_urgency = [
        "severe pain", "high fever", "vomiting blood", "difficulty breathing",
        "severe headache", "sudden weakness", "confusion"
    ]
    
    # Medium urgency symptoms
    medium_urgency = [
        "fever", "persistent cough", "moderate pain", "rash", "nausea",
        "dizziness", "fatigue"
    ]
    
    if any(indicator in symptoms_lower for indicator in emergency_indicators):
        return "emergency"
    elif any(indicator in symptoms_lower for indicator in high_urgency):
        return "high"
    elif any(indicator in symptoms_lower for indicator in medium_urgency):
        return "medium"
    else:
        return "low"


def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp for display.
    
    Args:
        timestamp: Datetime object
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")


def is_rate_limited(user_id: str, rate_limit_store: Dict[str, Any], 
                   max_requests: int = 60, window_minutes: int = 60) -> bool:
    """
    Check if user is rate limited.
    
    Args:
        user_id: User identifier
        rate_limit_store: In-memory rate limit storage
        max_requests: Maximum requests allowed
        window_minutes: Time window in minutes
        
    Returns:
        True if rate limited, False otherwise
    """
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)
    
    if user_id not in rate_limit_store:
        rate_limit_store[user_id] = []
    
    # Remove old requests outside the window
    rate_limit_store[user_id] = [
        req_time for req_time in rate_limit_store[user_id] 
        if req_time > window_start
    ]
    
    # Check if limit exceeded
    if len(rate_limit_store[user_id]) >= max_requests:
        return True
    
    # Add current request
    rate_limit_store[user_id].append(now)
    return False


def generate_conversation_id() -> str:
    """
    Generate a unique conversation ID.
    
    Returns:
        Unique conversation identifier
    """
    return f"conv_{secrets.token_hex(16)}"


def validate_conversation_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate conversation data before processing.
    
    Args:
        data: Conversation data dictionary
        
    Returns:
        Validation result
    """
    required_fields = ["user_id", "message", "timestamp"]
    
    for field in required_fields:
        if field not in data:
            return {"valid": False, "error": f"Missing required field: {field}"}
    
    # Validate message content
    if not data["message"] or len(data["message"].strip()) == 0:
        return {"valid": False, "error": "Message cannot be empty"}
    
    # Validate message length
    if len(data["message"]) > 5000:
        return {"valid": False, "error": "Message too long (max 5000 characters)"}
    
    # Sanitize message
    data["message"] = sanitize_input(data["message"])
    
    return {"valid": True, "data": data}


def log_medical_interaction(user_id: str, interaction_type: str, 
                          details: Dict[str, Any]) -> None:
    """
    Log medical interactions for audit purposes.
    
    Args:
        user_id: User identifier
        interaction_type: Type of interaction (chat, symptom_check, etc.)
        details: Additional details to log
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "interaction_type": interaction_type,
        "details": details
    }
    
    # Log with appropriate level based on interaction type
    if interaction_type == "emergency_detected":
        logger.warning(f"Emergency interaction logged: {log_data}")
    else:
        logger.info(f"Medical interaction logged: {log_data}")


def get_emergency_response() -> Dict[str, Any]:
    """
    Get standardized emergency response.
    
    Returns:
        Emergency response data
    """
    return {
        "message": (
            "⚠️ **EMERGENCY DETECTED** ⚠️\n\n"
            "Based on your symptoms, you may need immediate medical attention. "
            "Please contact emergency services or visit the nearest emergency room immediately.\n\n"
            "**Emergency Numbers:**\n"
            "• US: 911\n"
            "• UK: 999\n"
            "• EU: 112\n\n"
            "If you're experiencing a medical emergency, do not rely on this chatbot. "
            "Seek immediate professional medical help."
        ),
        "urgency": "emergency",
        "action_required": "immediate_medical_attention",
        "emergency_contacts": {
            "us": "911",
            "uk": "999",
            "eu": "112"
        }
    }


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive information in text for logging.
    
    Args:
        text: Text that may contain sensitive information
        
    Returns:
        Text with sensitive data masked
    """
    if not text:
        return text
    
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                  '[EMAIL_MASKED]', text)
    
    # Mask phone numbers
    text = re.sub(r'(\+?1-?)?(\(?[0-9]{3}\)?[-.\s]?){1,2}[0-9]{4}', 
                  '[PHONE_MASKED]', text)
    
    # Mask social security numbers
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_MASKED]', text)
    
    return text
