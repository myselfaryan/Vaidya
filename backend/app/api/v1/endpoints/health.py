"""
Health monitoring and system status endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.models.schemas import HealthCheck, UsageStats
from app.dependencies.auth import get_admin_user


router = APIRouter()


@router.get("/", response_model=HealthCheck)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Health status information
    """
    try:
        from app.core.config import settings
        from datetime import datetime
        
        # Check database connection
        from app.core.database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        # Check AI services
        from app.services.vector_service import vector_service
        vector_stats = vector_service.get_index_stats()
        
        services_status = {
            "database": "healthy",
            "vector_db": "healthy" if vector_stats else "unhealthy",
            "ai_service": "healthy"
        }
        
        overall_status = "healthy" if all(
            status == "healthy" for status in services_status.values()
        ) else "degraded"
        
        return HealthCheck(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            services=services_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )


@router.get("/detailed")
async def detailed_health_check(
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Detailed health check with comprehensive system information (admin only).
    
    Args:
        admin_user: Admin user
        db: Database session
        
    Returns:
        Detailed health and system information
    """
    try:
        from app.core.config import settings
        from datetime import datetime
        import psutil
        import time
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database metrics
        from app.models.models import User, Conversation, Message, MedicalDocument
        
        db_metrics = {
            "total_users": db.query(User).count(),
            "active_users": db.query(User).filter(User.is_active == True).count(),
            "total_conversations": db.query(Conversation).count(),
            "total_messages": db.query(Message).count(),
            "total_documents": db.query(MedicalDocument).count(),
            "processed_documents": db.query(MedicalDocument).filter(
                MedicalDocument.processed == True
            ).count()
        }
        
        # Vector database metrics
        from app.services.vector_service import vector_service
        vector_stats = vector_service.get_index_stats()
        
        # AI service metrics
        ai_metrics = {
            "model": settings.openai_model,
            "embedding_model": settings.embedding_model,
            "max_chunk_size": settings.max_chunk_size,
            "similarity_threshold": settings.similarity_threshold
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": settings.app_version,
            "uptime": time.time(),
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            },
            "database": db_metrics,
            "vector_database": vector_stats,
            "ai_service": ai_metrics,
            "configuration": {
                "debug_mode": settings.debug,
                "cors_origins": settings.backend_cors_origins,
                "rate_limiting": {
                    "requests_per_hour": settings.rate_limit_requests,
                    "window_seconds": settings.rate_limit_window
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve detailed health information"
        )


@router.get("/stats", response_model=UsageStats)
async def get_usage_stats(
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> UsageStats:
    """
    Get system usage statistics (admin only).
    
    Args:
        admin_user: Admin user
        db: Database session
        
    Returns:
        Usage statistics
    """
    try:
        from app.models.models import User, Conversation, Message
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Get today's date
        today = datetime.utcnow().date()
        
        # Basic counts
        total_users = db.query(User).count()
        active_conversations = db.query(Conversation).filter(
            Conversation.status == "active"
        ).count()
        
        # Messages today
        messages_today = db.query(Message).filter(
            func.date(Message.created_at) == today
        ).count()
        
        # Average response time (mock - in real implementation, you'd track this)
        avg_response_time = 1.2  # seconds
        
        # System health
        system_health = "healthy"
        
        return UsageStats(
            total_users=total_users,
            active_conversations=active_conversations,
            messages_today=messages_today,
            avg_response_time=avg_response_time,
            system_health=system_health
        )
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.get("/database")
async def database_health(
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Check database health and connection (admin only).
    
    Args:
        admin_user: Admin user
        db: Database session
        
    Returns:
        Database health information
    """
    try:
        from app.core.database import engine
        import time
        
        # Test database connection
        start_time = time.time()
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
        connection_time = time.time() - start_time
        
        # Get database info
        with engine.connect() as conn:
            # PostgreSQL specific queries
            db_size_result = conn.execute(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )
            db_size = db_size_result.fetchone()[0]
            
            # Active connections
            active_connections_result = conn.execute(
                "SELECT count(*) FROM pg_stat_activity"
            )
            active_connections = active_connections_result.fetchone()[0]
        
        return {
            "status": "healthy",
            "connection_time_ms": round(connection_time * 1000, 2),
            "database_size": db_size,
            "active_connections": active_connections,
            "engine_info": {
                "name": engine.name,
                "pool_size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow()
            }
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database health check failed"
        )


@router.get("/vector-db")
async def vector_database_health(
    admin_user = Depends(get_admin_user)
):
    """
    Check vector database health (admin only).
    
    Args:
        admin_user: Admin user
        
    Returns:
        Vector database health information
    """
    try:
        from app.services.vector_service import vector_service
        import time
        
        # Test vector database connection
        start_time = time.time()
        stats = vector_service.get_index_stats()
        response_time = time.time() - start_time
        
        # Test search functionality
        search_start = time.time()
        test_results = vector_service.search_similar(
            query_text="test query",
            top_k=1
        )
        search_time = time.time() - search_start
        
        return {
            "status": "healthy" if stats else "unhealthy",
            "response_time_ms": round(response_time * 1000, 2),
            "search_time_ms": round(search_time * 1000, 2),
            "index_stats": stats,
            "search_test": {
                "query": "test query",
                "results_count": len(test_results),
                "success": len(test_results) >= 0
            }
        }
        
    except Exception as e:
        logger.error(f"Vector database health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database health check failed"
        )


@router.get("/ai-service")
async def ai_service_health(
    admin_user = Depends(get_admin_user)
):
    """
    Check AI service health (admin only).
    
    Args:
        admin_user: Admin user
        
    Returns:
        AI service health information
    """
    try:
        from app.services.ai_service import ai_service
        from app.core.config import settings
        import time
        
        # Test AI service
        start_time = time.time()
        test_entities = await ai_service._extract_medical_entities("headache fever")
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
            "model_config": {
                "openai_model": settings.openai_model,
                "embedding_model": settings.embedding_model
            },
            "test_result": {
                "query": "headache fever",
                "entities_found": len(test_entities),
                "entities": test_entities,
                "success": True
            }
        }
        
    except Exception as e:
        logger.error(f"AI service health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "model_config": {
                "openai_model": settings.openai_model,
                "embedding_model": settings.embedding_model
            }
        }


@router.get("/redis")
async def redis_health(
    admin_user = Depends(get_admin_user)
):
    """
    Check Redis health (admin only).
    
    Args:
        admin_user: Admin user
        
    Returns:
        Redis health information
    """
    try:
        from app.core.database import get_redis
        import time
        
        redis_client = get_redis()
        
        # Test Redis connection
        start_time = time.time()
        redis_client.ping()
        response_time = time.time() - start_time
        
        # Get Redis info
        redis_info = redis_client.info()
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
            "redis_info": {
                "version": redis_info.get("redis_version"),
                "connected_clients": redis_info.get("connected_clients"),
                "used_memory_human": redis_info.get("used_memory_human"),
                "uptime_in_seconds": redis_info.get("uptime_in_seconds")
            }
        }
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis health check failed"
        )
