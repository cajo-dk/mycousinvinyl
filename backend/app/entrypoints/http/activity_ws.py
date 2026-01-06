"""
Activity websocket endpoints and broadcast manager.
"""

from typing import Dict, Any, List
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.config import get_settings, Settings
from app.entrypoints.http.auth import validate_token


class ActivityMessage(BaseModel):
    event_id: str | None = None
    event_type: str
    event_version: str
    occurred_at: str
    operation: str
    entity_type: str
    entity_id: str | None = None
    pressing_id: str | None = None
    album_id: str | None = None
    summary: str
    user_id: str | None = None
    user_name: str | None = None
    user_email: str | None = None


class ActivityConnectionManager:
    """Tracks active websocket connections and broadcasts messages."""

    def __init__(self) -> None:
        self._connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        async with self._lock:
            connections = list(self._connections)

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                await self.disconnect(websocket)


manager = ActivityConnectionManager()
router = APIRouter(tags=["Activity"])


@router.websocket("/ws/activity")
async def activity_ws(
    websocket: WebSocket,
    settings: Settings = Depends(get_settings),
):
    """Websocket endpoint for activity messages."""
    token = websocket.query_params.get("access_token") or websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        validate_token(token, settings)
    except HTTPException:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@router.post("/internal/activity", status_code=204)
async def publish_activity(
    message: ActivityMessage,
    settings: Settings = Depends(get_settings),
    x_activity_token: str | None = Header(default=None, alias="X-Activity-Token"),
):
    """Internal endpoint for the bridge worker to publish activity messages."""
    if not settings.activity_bridge_token or x_activity_token != settings.activity_bridge_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid activity token")

    await manager.broadcast(message.model_dump())
