"""
Main FastAPI application for the Vaidya medical chatbot.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

from .core.config import settings
from .core.database import init_db, close_db
from .api.v1.api import api_router
from .models.schemas import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    """
    # Startup
    logger.info("Starting Vaidya Medical Chatbot API...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Initialize AI services
        from .services.vector_service import vector_service
        from .services.ai_service import ai_service
        logger.info("AI services initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Vaidya Medical Chatbot API...")
        await close_db()
        logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered medical chatbot with RAG architecture for accurate healthcare information",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vaidya.ai"]
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    """Add unique request ID to responses."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for monitoring."""
    start_time = time.time()
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log request
    logger.info(
        f"Request started - ID: {request_id}, Method: {request.method}, "
        f"URL: {request.url}, Client: {request.client.host}"
    )
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Request completed - ID: {request_id}, Status: {response.status_code}, "
            f"Time: {process_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed - ID: {request_id}, Error: {str(e)}, "
            f"Time: {process_time:.3f}s"
        )
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail,
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception in request {request_id}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred",
            details={"request_id": request_id}
        ).dict()
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        from .core.database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        # Check AI services
        from .services.vector_service import vector_service
        vector_stats = vector_service.get_index_stats()
        
        services_status = {
            "database": "healthy",
            "vector_db": "healthy" if vector_stats else "unhealthy",
            "ai_service": "healthy"
        }
        
        overall_status = "healthy" if all(
            status == "healthy" for status in services_status.values()
        ) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "version": settings.app_version,
            "services": services_status
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "version": settings.app_version,
                "error": str(e)
            }
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else None,
        "medical_disclaimer": settings.medical_disclaimer
    }


# Include API router
app.include_router(api_router, prefix=settings.api_v1_str)


# Medical disclaimer endpoint
@app.get("/disclaimer")
async def get_disclaimer():
    """Get medical disclaimer information."""
    return {
        "disclaimer": settings.medical_disclaimer,
        "important_notes": [
            "This system provides educational information only",
            "Always consult healthcare professionals for medical decisions",
            "In case of emergency, contact emergency services immediately",
            "This AI assistant cannot replace professional medical diagnosis",
            "Individual medical situations may vary significantly"
        ],
        "emergency_contacts": {
            "us": "911",
            "uk": "999",
            "eu": "112",
            "general": "Contact your local emergency services"
        }
    }


# System information endpoint
@app.get("/system/info")
async def get_system_info():
    """Get system information (admin only in production)."""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        from .services.vector_service import vector_service
        vector_stats = vector_service.get_index_stats()
        
        return {
            "app_version": settings.app_version,
            "debug_mode": settings.debug,
            "vector_database": vector_stats,
            "ai_model": settings.openai_model,
            "embedding_model": settings.embedding_model,
            "max_chunk_size": settings.max_chunk_size,
            "similarity_threshold": settings.similarity_threshold
        }
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
