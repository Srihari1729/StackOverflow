from __future__ import annotations

import random
from typing import Dict, List, Optional

from app.domain.poker.engine import build_lobby_state, generate_room_code, start_demo_hand
from app.domain.poker.models import RoomConfig, RoomState, SeatState, SeatStatus


class RoomService:
    def __init__(self) -> None:
        self._rooms: Dict[str, RoomState] = {}
        self._rng = random.Random(1729)

    def list_rooms(self) -> List[RoomState]:
        return list(self._rooms.values())

    def get_room(self, room_code: str) -> Optional[RoomState]:
        return self._rooms.get(room_code)

    def create_room(self, host_session_id: str, host_name: str, config: RoomConfig) -> RoomState:
        room_code = self._next_room_code()
        room = build_lobby_state(room_code=room_code, host_session_id=host_session_id, host_name=host_name, config=config)
        room = start_demo_hand(room)
        self._rooms[room_code] = room
        return room

    def join_room(self, room_code: str, session_id: str, display_name: str) -> RoomState:
        room = self._rooms[room_code]
        open_seat_index = next((index for index, seat in enumerate(room.seats) if not seat.occupant_id), None)
        if open_seat_index is None:
            raise ValueError("Room is full")

        updated_seats = list(room.seats)
        updated_seats[open_seat_index] = SeatState(
            seat_index=open_seat_index,
            occupant_id=session_id,
            occupant_name=display_name,
            occupant_type="human",
            stack=2000,
            status=SeatStatus.READY,
        )
        updated_room = room.model_copy(update={"seats": updated_seats, "version": room.version + 1})
        self._rooms[room_code] = updated_room
        return updated_room

    def _next_room_code(self) -> str:
        while True:
            code = generate_room_code(self._rng)
            if code not in self._rooms:
                return code
