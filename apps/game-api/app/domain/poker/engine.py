from __future__ import annotations

import random
from typing import List

from .models import HandState, RoomConfig, RoomState, RoomStatus, SeatState, SeatStatus

BOT_NAMES = [
    "Pixel Shark",
    "Loose Mango",
    "Trap Door",
    "Night River",
    "Quiet Ember",
    "Mint Bluff",
]


def generate_room_code(rng: random.Random) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(rng.choice(alphabet) for _ in range(6))


def build_lobby_state(
    room_code: str,
    host_session_id: str,
    host_name: str,
    config: RoomConfig,
) -> RoomState:
    seats: List[SeatState] = [
        SeatState(
            seat_index=0,
            occupant_id=host_session_id,
            occupant_name=host_name,
            occupant_type="human",
            stack=2000,
            status=SeatStatus.READY,
        )
    ]

    for index in range(1, config.max_seats):
        if index <= config.bot_count:
            seats.append(
                SeatState(
                    seat_index=index,
                    occupant_id=f"bot_{index}",
                    occupant_name=BOT_NAMES[(index - 1) % len(BOT_NAMES)],
                    occupant_type="bot",
                    stack=2000,
                    status=SeatStatus.READY,
                )
            )
        else:
            seats.append(
                SeatState(
                    seat_index=index,
                    occupant_name="Open Seat",
                    occupant_type="human",
                    status=SeatStatus.WAITING,
                )
            )

    return RoomState(
        room_code=room_code,
        host_session_id=host_session_id,
        status=RoomStatus.LOBBY,
        config=config,
        seats=seats,
        hand_state=None,
        version=1,
    )


def start_demo_hand(room_state: RoomState) -> RoomState:
    active_seats = [seat for seat in room_state.seats if seat.occupant_id]
    if len(active_seats) < 2:
        return room_state

    updated_seats: List[SeatState] = []
    for seat in room_state.seats:
        if seat.occupant_id:
            cards = ["A♠", "K♦"] if seat.seat_index == 0 else ["?", "?"]
            updated_seats.append(
                seat.model_copy(
                    update={
                        "hole_cards": cards,
                        "status": SeatStatus.ACTING if seat.seat_index == 0 else SeatStatus.READY,
                    }
                )
            )
        else:
            updated_seats.append(seat)

    return room_state.model_copy(
        update={
            "status": RoomStatus.IN_PROGRESS,
            "seats": updated_seats,
            "hand_state": HandState(
                hand_id="hand_demo_001",
                street="river",
                pot_total=540,
                board=["Q♣", "J♥", "9♦", "3♠", "3♣"],
                acting_seat=0,
            ),
            "version": room_state.version + 1,
        }
    )
