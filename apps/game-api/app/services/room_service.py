from __future__ import annotations

from typing import Dict, List, Optional

from app.domain.bots.engine import choose_bot_action
from app.domain.poker.engine import apply_action, build_lobby_state, generate_room_code, legal_actions, start_new_hand
from app.domain.poker.models import ActionType, OccupantType, RoomConfig, RoomState, RoomStatus, SeatState, SeatStatus


class RoomService:
    def __init__(self) -> None:
        self._rooms: Dict[str, RoomState] = {}
        self._seed_counter = 1729

    def list_rooms(self) -> List[RoomState]:
        return list(self._rooms.values())

    def get_room(self, room_code: str) -> Optional[RoomState]:
        return self._rooms.get(room_code)

    def create_room(self, host_session_id: str, host_name: str, config: RoomConfig) -> RoomState:
        room_code = self._next_room_code()
        room = build_lobby_state(room_code=room_code, host_session_id=host_session_id, host_name=host_name, config=config)
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
            occupant_type=OccupantType.HUMAN,
            avatar_seed=display_name[:2].upper(),
            avatar_tone="#3f7cff",
            stack=room.config.starting_stack,
            status=SeatStatus.WAITING if room.status == RoomStatus.ACTIVE else SeatStatus.ACTIVE,
        )
        updated_room = room.model_copy(update={"seats": updated_seats, "version": room.version + 1})
        self._rooms[room_code] = updated_room
        return updated_room

    def start_hand(self, room_code: str, session_id: str) -> RoomState:
        room = self._rooms[room_code]
        if room.host_session_id != session_id:
            raise ValueError("Only the host can start the next hand")
        updated = start_new_hand(room)
        updated = self._run_bots(updated)
        self._rooms[room_code] = updated
        return updated

    def apply_player_action(self, room_code: str, session_id: str, action: ActionType, amount: int = 0) -> RoomState:
        room = self._rooms[room_code]
        if room.hand_state is None or room.hand_state.acting_seat is None:
            raise ValueError("No active turn")
        acting_seat = room.seats[room.hand_state.acting_seat]
        if acting_seat.occupant_id != session_id:
            raise ValueError("Session does not control the acting seat")
        updated = apply_action(room, acting_seat.seat_index, action, amount=amount)
        updated = self._run_bots(updated)
        self._rooms[room_code] = updated
        return updated

    def get_room_view(self, room_code: str, viewer_session_id: Optional[str] = None) -> RoomState:
        room = self._rooms[room_code]
        seats = []
        for seat in room.seats:
            reveal = seat.occupant_id == viewer_session_id or room.status == RoomStatus.HAND_OVER
            seats.append(
                seat.model_copy(
                    update={
                        "hole_cards": list(seat.hole_cards if reveal else ["XX", "XX"] if seat.hole_cards else []),
                    }
                )
            )
        return room.model_copy(update={"seats": seats})

    def legal_actions_for_session(self, room_code: str, session_id: str) -> List[ActionType]:
        room = self._rooms[room_code]
        if room.hand_state is None or room.hand_state.acting_seat is None:
            return []
        acting = room.seats[room.hand_state.acting_seat]
        if acting.occupant_id != session_id:
            return []
        return legal_actions(room, acting.seat_index)

    def _run_bots(self, room: RoomState) -> RoomState:
        current = room
        while (
            current.hand_state is not None
            and not current.hand_state.completed
            and current.hand_state.acting_seat is not None
        ):
            acting_seat = current.seats[current.hand_state.acting_seat]
            if acting_seat.occupant_type != OccupantType.BOT:
                break
            action, amount = choose_bot_action(current, acting_seat)
            current = apply_action(current, acting_seat.seat_index, action, amount=amount)
        return current

    def _next_room_code(self) -> str:
        while True:
            self._seed_counter += 1
            code = generate_room_code(self._seed_counter)
            if code not in self._rooms:
                return code
