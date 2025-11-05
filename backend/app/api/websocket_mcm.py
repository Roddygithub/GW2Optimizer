"""
WebSocket endpoint for McM (Mists of Castrum Marinum) Analytics.

This module provides real-time analytics data for World vs World combat.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import asyncio
import json
from datetime import datetime

from app.core.logging import logger
from app.services.mcm_analytics import McMAnalyticsService

router = APIRouter()

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    """Manages WebSocket connections for McM Analytics."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"📡 WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.remove(websocket)
        logger.info(f"📡 WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific connection."""
        await websocket.send_text(message)

    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected clients."""
        message_str = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")


manager = ConnectionManager()


@router.websocket("/ws/mcm")
async def websocket_mcm_analytics(websocket: WebSocket):
    """
    WebSocket endpoint for real-time McM analytics.

    Provides:
    - Real-time zerg tracking
    - Squad analytics
    - Battle metrics
    - Event notifications

    Example client usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/mcm');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('McM Analytics:', data);
    };
    ```
    """
    await manager.connect(websocket)

    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "status": "connected",
                "module": "McM Analytics",
                "timestamp": datetime.utcnow().isoformat(),
                "features": [
                    "zerg_tracking",
                    "squad_analytics",
                    "battle_metrics",
                    "event_notifications",
                ],
            }
        )

        # Initialize analytics service
        analytics_service = McMAnalyticsService()

        while True:
            # Wait for client messages or send periodic updates
            try:
                # Receive message from client (with timeout)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)

                # Process client request
                message = json.loads(data)
                request_type = message.get("type", "unknown")

                if request_type == "subscribe":
                    # Subscribe to specific analytics streams
                    streams = message.get("streams", [])
                    await websocket.send_json(
                        {
                            "type": "subscription_confirmed",
                            "streams": streams,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                elif request_type == "get_metrics":
                    # Get current metrics
                    metrics = await analytics_service.get_current_metrics()
                    await websocket.send_json(
                        {
                            "type": "metrics",
                            "data": metrics,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                elif request_type == "ping":
                    # Respond to ping
                    await websocket.send_json(
                        {
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

            except asyncio.TimeoutError:
                # Send periodic updates (every 5 seconds)
                metrics = await analytics_service.get_live_metrics()
                await websocket.send_json(
                    {
                        "type": "live_update",
                        "data": metrics,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from McM Analytics WebSocket")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/ws/mcm/events")
async def websocket_mcm_events(websocket: WebSocket):
    """
    WebSocket endpoint for McM event notifications.

    Provides real-time notifications for:
    - Capture events
    - Battle start/end
    - Objective changes
    - Commander movements
    """
    await manager.connect(websocket)

    try:
        await websocket.send_json(
            {
                "status": "connected",
                "module": "McM Events",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        while True:
            # Send event notifications
            await asyncio.sleep(10)  # Check for events every 10 seconds

            # In a real implementation, this would listen to an event queue
            event = {
                "type": "event_notification",
                "event": "capture",
                "objective": "Hills",
                "team": "Green",
                "timestamp": datetime.utcnow().isoformat(),
            }

            await websocket.send_json(event)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"WebSocket events error: {e}")
        manager.disconnect(websocket)


@router.get("/health")
async def websocket_health():
    """Health check endpoint for WebSocket service."""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "module": "McM WebSocket",
    }
