from app.domain.poker.evaluator import best_hand_rank
from app.domain.poker.models import ActionType, RoomConfig, RoomStatus, Street
from app.services.room_service import RoomService


def test_create_room_populates_lobby_with_host_and_bots() -> None:
    service = RoomService()
    room = service.create_room(
        host_session_id="session_1",
        host_name="Srihari",
        config=RoomConfig(max_seats=6, bot_count=4, small_blind=10, big_blind=20, difficulty="medium"),
    )

    assert room.room_code
    assert room.status == RoomStatus.LOBBY
    assert room.seats[0].occupant_name == "Srihari"
    assert len([seat for seat in room.seats if seat.occupant_id]) == 5
    assert room.hand_state is None


def test_start_hand_deals_cards_and_sets_turn() -> None:
    service = RoomService()
    room = service.create_room(
        host_session_id="session_1",
        host_name="Srihari",
        config=RoomConfig(max_seats=4, bot_count=2, small_blind=10, big_blind=20, difficulty="easy"),
    )

    started = service.start_hand(room.room_code, "session_1")

    assert started.status in (RoomStatus.ACTIVE, RoomStatus.HAND_OVER)
    assert started.hand_state is not None
    assert started.hand_state.street in (Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER, Street.COMPLETE)
    occupied = [seat for seat in started.seats if seat.occupant_id]
    assert all(len(seat.hole_cards) == 2 for seat in occupied)


def test_human_action_advances_game_state() -> None:
    service = RoomService()
    room = service.create_room(
        host_session_id="session_1",
        host_name="Srihari",
        config=RoomConfig(max_seats=4, bot_count=2, small_blind=10, big_blind=20, difficulty="medium"),
    )
    service.join_room(room.room_code, "session_2", "Ava")
    started = service.start_hand(room.room_code, "session_1")

    for _ in range(24):
        if started.hand_state is None or started.hand_state.completed:
            break
        acting_seat = started.seats[started.hand_state.acting_seat]
        if acting_seat.occupant_id == "session_1":
            legal = service.legal_actions_for_session(room.room_code, "session_1")
            if ActionType.CHECK in legal:
                started = service.apply_player_action(room.room_code, "session_1", ActionType.CHECK)
            else:
                started = service.apply_player_action(room.room_code, "session_1", ActionType.CALL)
        elif acting_seat.occupant_id == "session_2":
            legal = service.legal_actions_for_session(room.room_code, "session_2")
            if ActionType.CHECK in legal:
                started = service.apply_player_action(room.room_code, "session_2", ActionType.CHECK)
            else:
                started = service.apply_player_action(room.room_code, "session_2", ActionType.CALL)
        else:
            break

    assert started.hand_state is not None
    assert len(started.hand_state.action_log) > 0
    assert started.version > room.version


def test_hand_evaluator_ranks_flush_over_straight() -> None:
    flush = best_hand_rank(["As", "Ks", "Qs", "Ts", "2s", "9d", "3c"])
    straight = best_hand_rank(["9s", "8d", "7c", "6h", "5s", "2d", "3c"])
    assert flush > straight
