"""
Main API router for version 1 endpoints.
"""

from fastapi import APIRouter

from .endpoints import (
    auth,
    chat,
    documents,
    users,
    health,
    websocket
)

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Medical Chat"]
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Medical Documents"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health & Monitoring"]
)

api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"]
)
