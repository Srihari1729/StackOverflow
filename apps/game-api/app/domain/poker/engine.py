from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from .cards import shuffled_deck
from .evaluator import best_hand_rank
from .models import (
    ActionRecord,
    ActionType,
    BotDifficulty,
    BotPersonality,
    BotProfile,
    HandState,
    OccupantType,
    OpponentModel,
    PotState,
    RoomConfig,
    RoomState,
    RoomStatus,
    SeatState,
    SeatStatus,
    Street,
)

BOT_NAMES = [
    "Pixel Shark",
    "Loose Mango",
    "Trap Door",
    "Night River",
    "Quiet Ember",
    "Mint Bluff",
]
BOT_TONES = ["#8b5cf6", "#f97316", "#22c55e", "#ef4444", "#06b6d4", "#d946ef"]
BOT_PERSONALITIES = [
    BotPersonality.BALANCED,
    BotPersonality.LAG,
    BotPersonality.ROCK,
    BotPersonality.TRICKY,
    BotPersonality.STATION,
]


def generate_room_code(seed: int) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    value = seed
    chars = []
    for _ in range(6):
        chars.append(alphabet[value % len(alphabet)])
        value = (value * 17 + 23) % 100000
    return "".join(chars)


def build_lobby_state(room_code: str, host_session_id: str, host_name: str, config: RoomConfig) -> RoomState:
    seats: List[SeatState] = [
        SeatState(
            seat_index=0,
            occupant_id=host_session_id,
            occupant_name=host_name,
            occupant_type=OccupantType.HUMAN,
            avatar_seed=host_name[:2].upper(),
            avatar_tone="#3f7cff",
            stack=config.starting_stack,
            status=SeatStatus.WAITING,
        )
    ]
    for index in range(1, config.max_seats):
        if index <= config.bot_count:
            seats.append(
                SeatState(
                    seat_index=index,
                    occupant_id="bot_%s" % index,
                    occupant_name=BOT_NAMES[(index - 1) % len(BOT_NAMES)],
                    occupant_type=OccupantType.BOT,
                    avatar_seed=BOT_NAMES[(index - 1) % len(BOT_NAMES)][:2].upper(),
                    avatar_tone=BOT_TONES[(index - 1) % len(BOT_TONES)],
                    stack=config.starting_stack,
                    status=SeatStatus.WAITING,
                    bot_profile=BotProfile(
                        difficulty=config.difficulty,
                        personality=BOT_PERSONALITIES[(index - 1) % len(BOT_PERSONALITIES)],
                        avatar_seed=BOT_NAMES[(index - 1) % len(BOT_NAMES)][:2].upper(),
                        avatar_tone=BOT_TONES[(index - 1) % len(BOT_TONES)],
                    ),
                )
            )
        else:
            seats.append(
                SeatState(
                    seat_index=index,
                    occupant_name="Open Seat",
                    avatar_seed="OS",
                    avatar_tone="#475569",
                    status=SeatStatus.WAITING,
                )
            )
    return RoomState(room_code=room_code, host_session_id=host_session_id, config=config, seats=seats)


def occupied_playable_seats(room_state: RoomState) -> List[SeatState]:
    return [seat for seat in room_state.seats if seat.occupant_id and seat.stack > 0]


def next_occupied_index(room_state: RoomState, start_index: int, eligible: Iterable[int]) -> int:
    eligible_set = set(eligible)
    seat_count = len(room_state.seats)
    for offset in range(1, seat_count + 1):
        candidate = (start_index + offset) % seat_count
        if candidate in eligible_set:
            return candidate
    raise ValueError("No eligible seat found")


def _ordered_from(room_state: RoomState, start_index: int, eligible: Iterable[int]) -> List[int]:
    eligible_set = set(eligible)
    ordered: List[int] = []
    seat_count = len(room_state.seats)
    for offset in range(1, seat_count + 1):
        candidate = (start_index + offset) % seat_count
        if candidate in eligible_set:
            ordered.append(candidate)
    return ordered


def _bet(seat: SeatState, amount: int, forced_status: Optional[SeatStatus] = None) -> SeatState:
    clamped = min(amount, seat.stack)
    new_stack = seat.stack - clamped
    status = forced_status or (SeatStatus.ALL_IN if new_stack == 0 else SeatStatus.ACTIVE)
    return seat.model_copy(
        update={
            "stack": new_stack,
            "current_bet": seat.current_bet + clamped,
            "total_committed": seat.total_committed + clamped,
            "status": status,
            "has_acted": True,
        }
    )


def _reset_seat_for_new_hand(seat: SeatState) -> SeatState:
    if not seat.occupant_id:
        return seat.model_copy(
            update={
                "occupant_name": "Open Seat",
                "occupant_type": None,
                "status": SeatStatus.WAITING,
                "stack": 0,
                "hole_cards": [],
                "current_bet": 0,
                "total_committed": 0,
                "is_dealer": False,
                "is_small_blind": False,
                "is_big_blind": False,
                "has_acted": False,
            }
        )
    if seat.stack <= 0:
        return seat.model_copy(
            update={
                "status": SeatStatus.BUSTED,
                "hole_cards": [],
                "current_bet": 0,
                "total_committed": 0,
                "is_dealer": False,
                "is_small_blind": False,
                "is_big_blind": False,
                "has_acted": False,
            }
        )
    return seat.model_copy(
        update={
            "status": SeatStatus.ACTIVE,
            "hole_cards": [],
            "current_bet": 0,
            "total_committed": 0,
            "is_dealer": False,
            "is_small_blind": False,
            "is_big_blind": False,
            "has_acted": False,
        }
    )


def _apply_board_cards(hand_state: HandState, count: int) -> HandState:
    board = list(hand_state.board)
    deck = list(hand_state.deck)
    for _ in range(count):
        board.append(deck.pop(0))
    return hand_state.model_copy(update={"board": board, "deck": deck})


def _remaining_contenders(room_state: RoomState) -> List[SeatState]:
    return [seat for seat in room_state.seats if seat.occupant_id and seat.status not in (SeatStatus.FOLDED, SeatStatus.BUSTED)]


def _remaining_non_all_in(room_state: RoomState) -> List[SeatState]:
    return [seat for seat in _remaining_contenders(room_state) if seat.status == SeatStatus.ACTIVE and seat.stack > 0]


def _street_order(room_state: RoomState, dealer_seat: int) -> List[int]:
    contenders = [seat.seat_index for seat in room_state.seats if seat.occupant_id and seat.status == SeatStatus.ACTIVE and seat.stack > 0]
    return _ordered_from(room_state, dealer_seat, contenders)


def _append_action(hand_state: HandState, seat: SeatState, action: ActionType, amount: int = 0, target_bet: int = 0, note: str = "") -> HandState:
    record = ActionRecord(
        order=len(hand_state.action_log) + 1,
        seat_index=seat.seat_index,
        actor_name=seat.occupant_name,
        action=action,
        amount=amount,
        target_bet=target_bet,
        street=hand_state.street,
        note=note,
    )
    return hand_state.model_copy(update={"action_log": hand_state.action_log + [record]})


def _build_pots(room_state: RoomState) -> List[PotState]:
    committed = {seat.seat_index: seat.total_committed for seat in room_state.seats if seat.total_committed > 0}
    levels = sorted(set(committed.values()))
    previous = 0
    pots: List[PotState] = []
    for level in levels:
        contributors = [seat_index for seat_index, amount in committed.items() if amount >= level]
        eligible = [
            seat.seat_index
            for seat in room_state.seats
            if seat.seat_index in contributors and seat.status not in (SeatStatus.FOLDED, SeatStatus.BUSTED)
        ]
        amount = (level - previous) * len(contributors)
        if amount > 0:
            pots.append(PotState(amount=amount, eligible_seat_indices=eligible))
        previous = level
    return pots


def _hand_score(seat: SeatState, board: List[str]) -> Tuple[int, ...]:
    return best_hand_rank(seat.hole_cards + board)


def _settle_showdown(room_state: RoomState) -> RoomState:
    if room_state.hand_state is None:
        return room_state

    hand_state = room_state.hand_state
    while len(hand_state.board) < 5:
        hand_state = _apply_board_cards(hand_state, 1)

    pots = _build_pots(room_state)
    updated_seats = list(room_state.seats)
    winning_seats: List[int] = []
    win_fragments: List[str] = []
    for pot in pots:
        contenders = [updated_seats[index] for index in pot.eligible_seat_indices]
        if not contenders:
            continue
        scored = [(seat, _hand_score(seat, hand_state.board)) for seat in contenders]
        best = max(score for _, score in scored)
        winners = [seat for seat, score in scored if score == best]
        payout = pot.amount // len(winners)
        remainder = pot.amount % len(winners)
        for winner in winners:
            bonus = 1 if remainder > 0 else 0
            remainder -= bonus
            updated_seats[winner.seat_index] = winner.model_copy(update={"stack": winner.stack + payout + bonus})
            winning_seats.append(winner.seat_index)
        win_fragments.append("%s won %s" % (", ".join(winner.occupant_name for winner in winners), pot.amount))

    revealed = {
        seat.seat_index: list(seat.hole_cards)
        for seat in updated_seats
        if seat.occupant_id and seat.status not in (SeatStatus.FOLDED, SeatStatus.BUSTED)
    }

    normalized_seats = []
    for seat in updated_seats:
        if seat.occupant_id and seat.stack <= 0:
            normalized_seats.append(seat.model_copy(update={"status": SeatStatus.BUSTED, "current_bet": 0}))
        elif seat.occupant_id:
            normalized_seats.append(seat.model_copy(update={"current_bet": 0}))
        else:
            normalized_seats.append(seat)

    completed_hand = hand_state.model_copy(
        update={
            "street": Street.COMPLETE,
            "acting_seat": None,
            "current_bet": 0,
            "min_raise_to": 0,
            "pending_to_act": [],
            "winner_text": " | ".join(win_fragments),
            "winning_seat_indices": sorted(set(winning_seats)),
            "revealed_hole_cards": revealed,
            "pots": pots,
            "pot_total": sum(pot.amount for pot in pots),
            "completed": True,
        }
    )

    return room_state.model_copy(
        update={
            "status": RoomStatus.HAND_OVER,
            "seats": normalized_seats,
            "hand_state": completed_hand,
            "version": room_state.version + 1,
        }
    )


def _award_uncontested(room_state: RoomState, winner_seat: SeatState) -> RoomState:
    if room_state.hand_state is None:
        return room_state
    pot_total = sum(seat.total_committed for seat in room_state.seats)
    updated_seats = list(room_state.seats)
    updated_seats[winner_seat.seat_index] = winner_seat.model_copy(update={"stack": winner_seat.stack + pot_total})
    hand_state = room_state.hand_state.model_copy(
        update={
            "street": Street.COMPLETE,
            "acting_seat": None,
            "pot_total": pot_total,
            "winner_text": "%s won uncontested" % winner_seat.occupant_name,
            "winning_seat_indices": [winner_seat.seat_index],
            "pending_to_act": [],
            "completed": True,
        }
    )
    normalized = []
    for seat in updated_seats:
        if seat.occupant_id and seat.stack <= 0:
            normalized.append(seat.model_copy(update={"status": SeatStatus.BUSTED, "current_bet": 0}))
        elif seat.occupant_id:
            normalized.append(seat.model_copy(update={"current_bet": 0}))
        else:
            normalized.append(seat)
    return room_state.model_copy(update={"status": RoomStatus.HAND_OVER, "seats": normalized, "hand_state": hand_state, "version": room_state.version + 1})


def _advance_street(room_state: RoomState) -> RoomState:
    if room_state.hand_state is None:
        return room_state

    hand_state = room_state.hand_state
    next_street_map = {
        Street.PREFLOP: (Street.FLOP, 3),
        Street.FLOP: (Street.TURN, 1),
        Street.TURN: (Street.RIVER, 1),
    }

    if hand_state.street == Street.RIVER:
        return _settle_showdown(room_state)

    next_street, cards_to_add = next_street_map[hand_state.street]
    hand_state = _apply_board_cards(hand_state, cards_to_add)

    reset_seats: List[SeatState] = []
    for seat in room_state.seats:
        if seat.occupant_id and seat.status not in (SeatStatus.FOLDED, SeatStatus.BUSTED):
            status = SeatStatus.ALL_IN if seat.stack == 0 else SeatStatus.ACTIVE
            reset_seats.append(seat.model_copy(update={"current_bet": 0, "has_acted": False, "status": status}))
        else:
            reset_seats.append(seat.model_copy(update={"current_bet": 0}))

    room_state = room_state.model_copy(update={"seats": reset_seats})
    order = _street_order(room_state, hand_state.dealer_seat)
    acting = order[0] if order else None
    pending = list(order)
    updated_hand = hand_state.model_copy(
        update={
            "street": next_street,
            "acting_seat": acting,
            "current_bet": 0,
            "last_full_raise_size": room_state.config.big_blind,
            "min_raise_to": room_state.config.big_blind,
            "pending_to_act": pending,
            "pot_total": sum(seat.total_committed for seat in room_state.seats),
        }
    )
    updated_room = room_state.model_copy(update={"hand_state": updated_hand, "version": room_state.version + 1})
    if not pending:
        return _settle_showdown(updated_room)
    return updated_room


def _next_acting_from_pending(room_state: RoomState, current_seat: int) -> Optional[int]:
    if room_state.hand_state is None or not room_state.hand_state.pending_to_act:
        return None
    pending = room_state.hand_state.pending_to_act
    if current_seat in pending:
        current_index = pending.index(current_seat)
        if current_index + 1 < len(pending):
            return pending[current_index + 1]
    return pending[0]


def start_new_hand(room_state: RoomState) -> RoomState:
    eligible_seats = [seat.seat_index for seat in occupied_playable_seats(room_state)]
    if len(eligible_seats) < 2:
        return room_state.model_copy(update={"status": RoomStatus.LOBBY, "hand_state": None, "version": room_state.version + 1})

    previous_dealer = room_state.hand_state.dealer_seat if room_state.hand_state else -1
    dealer_seat = next_occupied_index(room_state, previous_dealer, eligible_seats)
    if len(eligible_seats) == 2:
        small_blind_seat = dealer_seat
        big_blind_seat = next_occupied_index(room_state, dealer_seat, eligible_seats)
    else:
        small_blind_seat = next_occupied_index(room_state, dealer_seat, eligible_seats)
        big_blind_seat = next_occupied_index(room_state, small_blind_seat, eligible_seats)

    seat_updates = [_reset_seat_for_new_hand(seat) for seat in room_state.seats]
    room_state = room_state.model_copy(update={"seats": seat_updates})
    deck = shuffled_deck(room_state.hand_counter + 1)

    active_order = _ordered_from(room_state, dealer_seat - 1, eligible_seats)
    for _ in range(2):
        for seat_index in active_order:
            seat = room_state.seats[seat_index]
            room_state.seats[seat_index] = seat.model_copy(update={"hole_cards": seat.hole_cards + [deck.pop(0)]})

    seat_updates = list(room_state.seats)
    seat_updates[dealer_seat] = seat_updates[dealer_seat].model_copy(update={"is_dealer": True})
    seat_updates[small_blind_seat] = _bet(seat_updates[small_blind_seat].model_copy(update={"is_small_blind": True}), room_state.config.small_blind)
    seat_updates[big_blind_seat] = _bet(seat_updates[big_blind_seat].model_copy(update={"is_big_blind": True}), room_state.config.big_blind)

    acting_order = _ordered_from(room_state, big_blind_seat, [seat.seat_index for seat in seat_updates if seat.occupant_id and seat.status == SeatStatus.ACTIVE and seat.stack > 0])
    hand_state = HandState(
        hand_id="hand_%03d" % (room_state.hand_counter + 1),
        hand_number=room_state.hand_counter + 1,
        street=Street.PREFLOP,
        dealer_seat=dealer_seat,
        small_blind_seat=small_blind_seat,
        big_blind_seat=big_blind_seat,
        acting_seat=acting_order[0] if acting_order else None,
        board=[],
        deck=deck,
        pot_total=room_state.config.small_blind + room_state.config.big_blind,
        current_bet=room_state.config.big_blind,
        last_full_raise_size=room_state.config.big_blind,
        min_raise_to=room_state.config.big_blind * 2,
        pending_to_act=acting_order,
        action_log=[],
    )
    started = room_state.model_copy(
        update={
            "status": RoomStatus.ACTIVE,
            "seats": seat_updates,
            "hand_state": hand_state,
            "hand_counter": room_state.hand_counter + 1,
            "version": room_state.version + 1,
        }
    )
    return started


def legal_actions(room_state: RoomState, seat_index: int) -> List[ActionType]:
    if room_state.hand_state is None or room_state.hand_state.acting_seat != seat_index:
        return []
    seat = room_state.seats[seat_index]
    to_call = max(0, room_state.hand_state.current_bet - seat.current_bet)
    actions: List[ActionType] = [ActionType.FOLD]
    if to_call == 0:
        actions.append(ActionType.CHECK)
    else:
        actions.append(ActionType.CALL)
    if seat.stack > to_call:
        actions.append(ActionType.RAISE)
        actions.append(ActionType.ALL_IN)
    return actions


def update_opponent_model(room_state: RoomState, actor: SeatState, action: ActionType, amount: int) -> RoomState:
    bot_memories = dict(room_state.bot_memories)
    for seat in room_state.seats:
        if seat.occupant_type != OccupantType.BOT or not seat.occupant_id or seat.occupant_id == actor.occupant_id:
            continue
        seat_memory = dict(bot_memories.get(seat.occupant_id, {}))
        model = seat_memory.get(actor.occupant_id, OpponentModel())
        new_hands = model.hands_observed + 1
        vpip = ((model.vpip * model.hands_observed) + (1.0 if amount > 0 else 0.0)) / new_hands
        pfr = ((model.pfr * model.hands_observed) + (1.0 if action in (ActionType.RAISE, ActionType.ALL_IN) else 0.0)) / new_hands
        aggression = ((model.aggression * model.hands_observed) + (2.0 if action in (ActionType.RAISE, ActionType.ALL_IN) else 0.6)) / new_hands
        seat_memory[actor.occupant_id] = model.model_copy(update={"hands_observed": new_hands, "vpip": vpip, "pfr": pfr, "aggression": aggression})
        bot_memories[seat.occupant_id] = seat_memory
    return room_state.model_copy(update={"bot_memories": bot_memories})


def apply_action(room_state: RoomState, seat_index: int, action: ActionType, amount: int = 0) -> RoomState:
    if room_state.hand_state is None or room_state.hand_state.completed:
        raise ValueError("No active hand")
    if room_state.hand_state.acting_seat != seat_index:
        raise ValueError("It is not this seat's turn")

    seat = room_state.seats[seat_index]
    hand_state = room_state.hand_state
    to_call = max(0, hand_state.current_bet - seat.current_bet)
    seat_updates = list(room_state.seats)
    pending = [index for index in hand_state.pending_to_act if index != seat_index]

    if action == ActionType.FOLD:
        updated_seat = seat.model_copy(update={"status": SeatStatus.FOLDED, "has_acted": True})
        seat_updates[seat_index] = updated_seat
        hand_state = _append_action(hand_state, seat, action)
    elif action == ActionType.CHECK:
        if to_call != 0:
            raise ValueError("Cannot check facing a bet")
        updated_seat = seat.model_copy(update={"has_acted": True})
        seat_updates[seat_index] = updated_seat
        hand_state = _append_action(hand_state, seat, action)
    elif action == ActionType.CALL:
        if to_call == 0:
            raise ValueError("Nothing to call")
        updated_seat = _bet(seat, to_call)
        seat_updates[seat_index] = updated_seat
        hand_state = _append_action(hand_state, seat, ActionType.CALL, amount=min(to_call, seat.stack), target_bet=updated_seat.current_bet)
    elif action in (ActionType.RAISE, ActionType.ALL_IN):
        max_target = seat.current_bet + seat.stack
        target_bet = max_target if action == ActionType.ALL_IN else amount
        if target_bet <= hand_state.current_bet or target_bet <= seat.current_bet:
            raise ValueError("Raise target is too small")
        if target_bet > max_target:
            raise ValueError("Raise exceeds stack")
        additional = target_bet - seat.current_bet
        updated_seat = _bet(seat, additional)
        seat_updates[seat_index] = updated_seat
        raise_size = target_bet - hand_state.current_bet
        full_raise = hand_state.current_bet == 0 or raise_size >= hand_state.last_full_raise_size
        other_players = [
            candidate.seat_index
            for candidate in seat_updates
            if candidate.occupant_id and candidate.seat_index != seat_index and candidate.status == SeatStatus.ACTIVE and candidate.stack > 0
        ]
        pending = _ordered_from(room_state.model_copy(update={"seats": seat_updates}), seat_index, other_players)
        hand_state = _append_action(
            hand_state,
            seat,
            ActionType.ALL_IN if updated_seat.stack == 0 else ActionType.RAISE,
            amount=additional,
            target_bet=target_bet,
            note="short all-in" if updated_seat.stack == 0 and not full_raise else "",
        )
        if full_raise:
            hand_state = hand_state.model_copy(
                update={
                    "current_bet": target_bet,
                    "last_full_raise_size": raise_size if hand_state.current_bet > 0 else target_bet,
                    "min_raise_to": target_bet + (raise_size if raise_size > 0 else room_state.config.big_blind),
                }
            )
        else:
            hand_state = hand_state.model_copy(update={"current_bet": target_bet, "min_raise_to": target_bet + hand_state.last_full_raise_size})
    else:
        raise ValueError("Unsupported action")

    updated_room = room_state.model_copy(update={"seats": seat_updates, "hand_state": hand_state})
    updated_room = update_opponent_model(updated_room, seat, action, amount if amount else to_call)
    contenders = _remaining_contenders(updated_room)
    if len(contenders) == 1:
        return _award_uncontested(updated_room, contenders[0])

    updated_hand = updated_room.hand_state.model_copy(update={"pending_to_act": pending})
    next_actor = pending[0] if pending else None
    updated_room = updated_room.model_copy(
        update={
            "hand_state": updated_hand.model_copy(update={"acting_seat": next_actor, "pot_total": sum(state.total_committed for state in updated_room.seats)}),
            "version": updated_room.version + 1,
        }
    )

    if not pending or not _remaining_non_all_in(updated_room):
        return _advance_street(updated_room)
    return updated_room
