from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import register_routes
from app.services.mock_auth_service import MockAuthService
from app.services.room_service import RoomService

app = FastAPI(title="Premium Poker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_service = MockAuthService()
room_service = RoomService()
register_routes(app, auth_service=auth_service, room_service=room_service)
