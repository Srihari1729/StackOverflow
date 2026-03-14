from __future__ import annotations

import random
from typing import Dict, List, Tuple

from app.domain.poker.cards import full_deck, remove_cards
from app.domain.poker.evaluator import best_hand_rank
from app.domain.poker.models import ActionType, BotDifficulty, BotPersonality, OccupantType, RoomState, SeatState, SeatStatus, Street


def _preflop_strength(hole_cards: List[str]) -> float:
    values = sorted(["23456789TJQKA".index(card[0]) + 2 for card in hole_cards], reverse=True)
    suited = hole_cards[0][1] == hole_cards[1][1]
    pair = values[0] == values[1]
    connected = abs(values[0] - values[1]) <= 2
    score = (values[0] + values[1]) / 28.0
    if pair:
        score += 0.35
    if suited:
        score += 0.08
    if connected:
        score += 0.05
    return min(score, 0.99)


def _postflop_equity(room_state: RoomState, seat: SeatState, iterations: int, rng: random.Random) -> float:
    if room_state.hand_state is None:
        return 0.0

    board = list(room_state.hand_state.board)
    known_cards = board + list(seat.hole_cards)
    other_count = len(
        [
            contender
            for contender in room_state.seats
            if contender.occupant_id
            and contender.seat_index != seat.seat_index
            and contender.status not in (SeatStatus.FOLDED, SeatStatus.BUSTED)
        ]
    )
    if other_count <= 0:
        return 1.0

    deck = remove_cards(full_deck(), known_cards)
    wins = 0.0
    for _ in range(iterations):
        rng.shuffle(deck)
        cursor = 0
        opponent_hands = []
        for _opponent_index in range(other_count):
            opponent_hands.append(deck[cursor : cursor + 2])
            cursor += 2

        simulated_board = list(board)
        while len(simulated_board) < 5:
            simulated_board.append(deck[cursor])
            cursor += 1

        hero_score = best_hand_rank(seat.hole_cards + simulated_board)
        opponent_scores = [best_hand_rank(cards + simulated_board) for cards in opponent_hands]
        best_score = max([hero_score] + opponent_scores)
        winners = 1 + sum(1 for score in opponent_scores if score == best_score) if hero_score == best_score else sum(1 for score in opponent_scores if score == best_score)
        if hero_score == best_score:
            wins += 1.0 / winners
    return wins / float(iterations)


def estimate_strength(room_state: RoomState, seat: SeatState, difficulty: BotDifficulty) -> float:
    if room_state.hand_state is None:
        return 0.0
    if room_state.hand_state.street == Street.PREFLOP:
        return _preflop_strength(seat.hole_cards)

    iterations = {BotDifficulty.EASY: 60, BotDifficulty.MEDIUM: 120, BotDifficulty.HARD: 180}[difficulty]
    seed = (room_state.version * 97) + (seat.seat_index * 17) + room_state.hand_state.hand_number
    return _postflop_equity(room_state, seat, iterations=iterations, rng=random.Random(seed))


def choose_bot_action(room_state: RoomState, seat: SeatState) -> Tuple[ActionType, int]:
    if room_state.hand_state is None or seat.bot_profile is None:
        raise ValueError("Bot seat or hand missing")

    difficulty = seat.bot_profile.difficulty
    personality = seat.bot_profile.personality
    strength = estimate_strength(room_state, seat, difficulty)
    to_call = max(0, room_state.hand_state.current_bet - seat.current_bet)
    pot_total = max(room_state.hand_state.pot_total, room_state.config.big_blind * 2)
    rng = random.Random((room_state.version * 131) + (seat.seat_index * 11))

    personality_shift: Dict[BotPersonality, float] = {
        BotPersonality.ROCK: -0.12,
        BotPersonality.BALANCED: 0.0,
        BotPersonality.LAG: 0.1,
        BotPersonality.TRICKY: 0.04,
        BotPersonality.STATION: -0.03,
    }
    noise = {BotDifficulty.EASY: 0.16, BotDifficulty.MEDIUM: 0.1, BotDifficulty.HARD: 0.06}[difficulty]
    adjusted_strength = max(0.0, min(0.99, strength + personality_shift[personality] + rng.uniform(-noise, noise)))

    if to_call == 0:
        if adjusted_strength > 0.74 and seat.stack > room_state.config.big_blind:
            raise_size = int(pot_total * (0.55 if personality == BotPersonality.ROCK else 0.75))
            target = max(room_state.config.big_blind, raise_size)
            return ActionType.RAISE, target
        if personality == BotPersonality.TRICKY and adjusted_strength > 0.55 and rng.random() < 0.25:
            return ActionType.RAISE, max(room_state.config.big_blind, int(pot_total * 0.4))
        return ActionType.CHECK, 0

    pot_odds = float(to_call) / float(pot_total + to_call)
    if adjusted_strength + 0.08 < pot_odds and rng.random() > 0.15:
        return ActionType.FOLD, 0

    if adjusted_strength > 0.82 and seat.stack > to_call + room_state.config.big_blind:
        raise_multiplier = 0.75 if difficulty == BotDifficulty.HARD else 0.55
        raise_size = max(room_state.config.big_blind * 2, int((pot_total + to_call) * raise_multiplier))
        target = room_state.hand_state.current_bet + raise_size
        if target >= seat.current_bet + seat.stack:
            return ActionType.ALL_IN, seat.current_bet + seat.stack
        return ActionType.RAISE, target

    if adjusted_strength > 0.45 or personality == BotPersonality.STATION:
        if seat.stack <= to_call:
            return ActionType.ALL_IN, seat.current_bet + seat.stack
        return ActionType.CALL, 0

    return ActionType.FOLD, 0
