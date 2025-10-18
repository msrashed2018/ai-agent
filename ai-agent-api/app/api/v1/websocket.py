"""
WebSocket API endpoints for real-time session streaming.
"""

import json
from typing import Dict, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_websocket_user, get_db_session
from app.domain.entities import User
from app.repositories.session_repository import SessionRepository
from app.services.sdk_session_service import SDKIntegratedSessionService
from app.claude_sdk.message_processor import EventBroadcaster
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(tags=["websocket"])


# Global event broadcaster instance
event_broadcaster = EventBroadcaster()


@router.websocket("/sessions/{session_id}/stream")
async def websocket_session_stream(
    websocket: WebSocket,
    session_id: UUID,
    token: str = Query(..., description="JWT authentication token"),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    WebSocket endpoint for real-time session message streaming.
    
    **Connection:**
    ```javascript
    const ws = new WebSocket(
        'ws://api/v1/sessions/{session_id}/stream?token=<jwt_token>'
    );
    ```
    
    **Send Message:**
    ```json
    {
        "type": "query",
        "message": "What is the current CPU usage?"
    }
    ```
    
    **Receive Messages:**
    - `message`: New message received
    - `status_change`: Session status changed
    - `tool_call_started`: Tool execution started
    - `tool_call_completed`: Tool execution completed
    - `error`: Error occurred
    """
    await websocket.accept()
    
    try:
        # Authenticate user
        current_user = await get_websocket_user(websocket, token, db)
        
        # Verify session ownership
        repo = SessionRepository(db)
        session = await repo.get_by_id(str(session_id))
        
        if session is None:
            await websocket.send_json({
                "type": "error",
                "data": {
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Session {session_id} not found",
                }
            })
            await websocket.close(code=1008, reason="Session not found")
            return
        
        if session.user_id != current_user.id and current_user.role != "admin":
            await websocket.send_json({
                "type": "error",
                "data": {
                    "code": "FORBIDDEN",
                    "message": "Not authorized to access this session",
                }
            })
            await websocket.close(code=1008, reason="Not authorized")
            return
        
        # Subscribe to session events
        subscriber_id = event_broadcaster.subscribe(str(session_id))
        logger.info(f"WebSocket client connected to session {session_id}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {
                "session_id": str(session_id),
                "status": session.status,
            }
        })
        
        # Initialize service
        service = SDKIntegratedSessionService(db)
        
        # Main message loop
        while True:
            try:
                # Wait for message from client
                raw_data = await websocket.receive_text()
                data = json.loads(raw_data)
                
                message_type = data.get("type")
                
                if message_type == "query":
                    # Send message to Claude
                    message_content = data.get("message")
                    if not message_content:
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "code": "INVALID_INPUT",
                                "message": "Message content required",
                            }
                        })
                        continue
                    
                    # Send message (this will trigger events through EventBroadcaster)
                    message = await service.send_message(
                        session_id=str(session_id),
                        message_content=message_content,
                    )
                    
                    # Confirm message sent
                    await websocket.send_json({
                        "type": "message_sent",
                        "data": {
                            "message_id": str(message.id),
                            "status": "processing",
                        }
                    })
                
                elif message_type == "ping":
                    # Heartbeat
                    await websocket.send_json({"type": "pong"})
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "data": {
                            "code": "UNKNOWN_MESSAGE_TYPE",
                            "message": f"Unknown message type: {message_type}",
                        }
                    })
            
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected from session {session_id}")
                break
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "code": "INVALID_JSON",
                        "message": "Invalid JSON message",
                    }
                })
            
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "code": "INTERNAL_ERROR",
                        "message": str(e),
                    }
                })
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except Exception:
            pass
    
    finally:
        # Unsubscribe from events
        if 'subscriber_id' in locals():
            event_broadcaster.unsubscribe(str(session_id), subscriber_id)
        
        logger.info(f"WebSocket connection closed for session {session_id}")


async def broadcast_session_event(
    session_id: str,
    event_type: str,
    data: Dict,
) -> None:
    """
    Broadcast an event to all WebSocket clients connected to a session.
    
    Args:
        session_id: Session UUID
        event_type: Event type (message, status_change, tool_call_started, etc.)
        data: Event data
    """
    message = {
        "type": event_type,
        "data": data,
    }
    await event_broadcaster.broadcast_message(session_id, message)
