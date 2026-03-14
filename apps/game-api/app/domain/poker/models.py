from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SeatStatus(str, Enum):
    READY = "ready"
    ACTING = "acting"
    FOLDED = "folded"
    WAITING = "waiting"


class RoomStatus(str, Enum):
    LOBBY = "lobby"
    IN_PROGRESS = "in_progress"


class SeatState(BaseModel):
    seat_index: int
    occupant_id: Optional[str] = None
    occupant_name: str
    occupant_type: str = "human"
    stack: int = 0
    status: SeatStatus = SeatStatus.WAITING
    hole_cards: List[str] = Field(default_factory=list)


class HandState(BaseModel):
    hand_id: str
    street: str = "preflop"
    pot_total: int = 0
    board: List[str] = Field(default_factory=list)
    acting_seat: Optional[int] = None
    legal_actions: List[str] = Field(default_factory=lambda: ["fold", "call", "raise"])


class RoomConfig(BaseModel):
    max_seats: int = Field(6, ge=2, le=6)
    bot_count: int = Field(4, ge=0, le=5)
    small_blind: int = Field(10, gt=0)
    big_blind: int = Field(20, gt=0)
    difficulty: str = "medium"


class RoomState(BaseModel):
    room_code: str
    host_session_id: str
    status: RoomStatus = RoomStatus.LOBBY
    config: RoomConfig
    seats: List[SeatState]
    hand_state: Optional[HandState] = None
    version: int = 1
