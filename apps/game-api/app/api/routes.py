from __future__ import annotations

import asyncio
from typing import List, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.domain.poker.models import ActionType, RoomConfig, RoomState
from app.services.mock_auth_service import MockAuthService
from app.services.room_service import RoomService


class CreateSessionRequest(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=24)


class SessionResponse(BaseModel):
    session_id: str
    display_name: str


class CreateRoomRequest(BaseModel):
    session_id: str
    config: RoomConfig


class JoinRoomRequest(BaseModel):
    session_id: str
    room_code: str


class PlayerActionRequest(BaseModel):
    session_id: str
    action: ActionType
    amount: int = 0


class RoomViewResponse(BaseModel):
    room: RoomState
    legal_actions: List[ActionType]


def register_routes(app: FastAPI, auth_service: MockAuthService, room_service: RoomService) -> None:
    router = APIRouter()

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/mock-auth/sessions", response_model=SessionResponse)
    async def create_session(payload: CreateSessionRequest) -> SessionResponse:
        session = auth_service.create_session(payload.display_name.strip())
        return SessionResponse(session_id=session.session_id, display_name=session.display_name)

    @router.get("/rooms", response_model=List[RoomState])
    async def list_rooms() -> List[RoomState]:
        return room_service.list_rooms()

    @router.post("/rooms", response_model=RoomState)
    async def create_room(payload: CreateRoomRequest) -> RoomState:
        session = auth_service.get_session(payload.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Unknown session")
        return room_service.create_room(host_session_id=session.session_id, host_name=session.display_name, config=payload.config)

    @router.post("/rooms/join", response_model=RoomState)
    async def join_room(payload: JoinRoomRequest) -> RoomState:
        session = auth_service.get_session(payload.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Unknown session")
        room = room_service.get_room(payload.room_code)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        try:
            return room_service.join_room(payload.room_code, session.session_id, session.display_name)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @router.post("/rooms/{room_code}/start", response_model=RoomState)
    async def start_hand(room_code: str, session_id: str = Query(...)) -> RoomState:
        try:
            return room_service.start_hand(room_code, session_id)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @router.post("/rooms/{room_code}/actions", response_model=RoomState)
    async def player_action(room_code: str, payload: PlayerActionRequest) -> RoomState:
        try:
            return room_service.apply_player_action(room_code, payload.session_id, payload.action, payload.amount)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @router.get("/rooms/{room_code}", response_model=RoomViewResponse)
    async def get_room(room_code: str, session_id: Optional[str] = None) -> RoomViewResponse:
        room = room_service.get_room(room_code)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return RoomViewResponse(
            room=room_service.get_room_view(room_code, viewer_session_id=session_id),
            legal_actions=room_service.legal_actions_for_session(room_code, session_id or ""),
        )

    app.include_router(router, prefix="/api")

    @app.websocket("/ws/rooms/{room_code}")
    async def room_stream(websocket: WebSocket, room_code: str) -> None:
        await websocket.accept()
        session_id = websocket.query_params.get("session_id")
        try:
            while True:
                room = room_service.get_room(room_code)
                if room is None:
                    await websocket.send_json({"type": "room.missing", "roomCode": room_code})
                    break
                view = room_service.get_room_view(room_code, viewer_session_id=session_id)
                await websocket.send_json(
                    {
                        "type": "table.state",
                        "roomCode": room_code,
                        "version": view.version,
                        "room": view.model_dump(mode="json"),
                        "legalActions": [action.value for action in room_service.legal_actions_for_session(room_code, session_id or "")],
                    }
                )
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            return
