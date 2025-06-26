"""
Core configuration settings for the Vaidya medical chatbot system.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_name: str = "Vaidya Medical Chatbot"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API
    api_v1_str: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    backend_cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000",
        "https://localhost:8000",
    ]
    
    # Database
    database_url: str = Field(..., description="PostgreSQL database URL")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    
    # AI Services
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    
    # Vector Database
    pinecone_api_key: str = Field(..., description="Pinecone API key")
    pinecone_environment: str = Field(..., description="Pinecone environment")
    pinecone_index_name: str = "vaidya-medical-knowledge"
    
    # Medical Processing
    max_chunk_size: int = 1000
    chunk_overlap: int = 200
    max_retrieval_results: int = 5
    similarity_threshold: float = 0.7
    
    # File Upload
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: List[str] = [".pdf", ".docx", ".txt", ".md"]
    
    # WebSocket
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Medical Compliance
    medical_disclaimer: str = (
        "This information is for educational purposes only and should not "
        "replace professional medical advice, diagnosis, or treatment. "
        "Always consult with a qualified healthcare provider for medical concerns."
    )
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    class Config:
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
