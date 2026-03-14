from app.domain.poker.models import RoomConfig
from app.services.room_service import RoomService


def test_create_room_populates_host_and_bots() -> None:
    service = RoomService()
    room = service.create_room(
        host_session_id="session_1",
        host_name="Srihari",
        config=RoomConfig(max_seats=6, bot_count=4, small_blind=10, big_blind=20, difficulty="medium"),
    )

    assert room.room_code
    assert room.seats[0].occupant_name == "Srihari"
    assert room.hand_state is not None
    assert len([seat for seat in room.seats if seat.occupant_id]) == 5
