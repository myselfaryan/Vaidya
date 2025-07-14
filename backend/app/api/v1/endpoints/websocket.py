"""
WebSocket endpoints for real-time chat capabilities.
"""

from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from loguru import logger

from app.dependencies.auth import get_current_user_optional
from app.models.models import User


router = APIRouter()

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str) -> None:
        self.active_connections.pop(client_id, None)
    
    async def send_personal_message(self, message: str, client_id: str) -> None:
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_text(message)
    
    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections.values():
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/chat/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    current_user: User = Depends(get_current_user_optional)
):
    """
    WebSocket endpoint for real-time chat.
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
        current_user: Current authenticated user (optional)
    """
    await manager.connect(websocket, client_id)
    
    user_id = current_user.id if current_user else "guest"
    logger.info(f"Client connected: {client_id}, User: {user_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from {client_id}: {data}")
            await manager.send_personal_message(f"Echo: {data}", client_id)
            await manager.broadcast(f"Broadcast: {client_id} says {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client disconnected: {client_id}")
        await manager.broadcast(f"Client {client_id} disconnected")
        
    except Exception as e:
        logger.error(f"Error on WebSocket: {str(e)}")
        await manager.disconnect(client_id)

