from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence, Tuple

from .cards import card_rank, card_suit

RANK_VALUE = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}


def _straight_high(values: Sequence[int]) -> int:
    unique_values = sorted(set(values), reverse=True)
    if 14 in unique_values:
        unique_values.append(1)

    run = 1
    best = 0
    for index in range(1, len(unique_values)):
        if unique_values[index - 1] - 1 == unique_values[index]:
            run += 1
            if run >= 5:
                best = unique_values[index - 4]
        else:
            run = 1
    return best


def _five_card_rank(cards: Sequence[str]) -> Tuple[int, ...]:
    values = sorted((RANK_VALUE[card_rank(card)] for card in cards), reverse=True)
    suits = [card_suit(card) for card in cards]
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1

    groups = sorted(((count, value) for value, count in counts.items()), reverse=True)
    flush = len(set(suits)) == 1
    straight_high = _straight_high(values)

    if flush and straight_high:
        return (8, straight_high)

    if groups[0][0] == 4:
        quad = groups[0][1]
        kicker = max(value for value in values if value != quad)
        return (7, quad, kicker)

    if groups[0][0] == 3 and len(groups) > 1 and groups[1][0] >= 2:
        return (6, groups[0][1], groups[1][1])

    if flush:
        return (5,) + tuple(values)

    if straight_high:
        return (4, straight_high)

    if groups[0][0] == 3:
        trip = groups[0][1]
        kickers = sorted((value for value in values if value != trip), reverse=True)
        return (3, trip) + tuple(kickers)

    if groups[0][0] == 2 and len(groups) > 1 and groups[1][0] == 2:
        pair_values = sorted((groups[0][1], groups[1][1]), reverse=True)
        kicker = max(value for value in values if value not in pair_values)
        return (2, pair_values[0], pair_values[1], kicker)

    if groups[0][0] == 2:
        pair = groups[0][1]
        kickers = sorted((value for value in values if value != pair), reverse=True)
        return (1, pair) + tuple(kickers)

    return (0,) + tuple(values)


def best_hand_rank(cards: Iterable[str]) -> Tuple[int, ...]:
    best = None
    card_list = list(cards)
    for combo in combinations(card_list, 5):
        rank = _five_card_rank(combo)
        if best is None or rank > best:
            best = rank
    if best is None:
        raise ValueError("At least five cards are required")
    return best
