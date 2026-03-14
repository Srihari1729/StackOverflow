from __future__ import annotations

import random
from typing import Iterable, List

RANKS = "23456789TJQKA"
SUITS = "shdc"


def full_deck() -> List[str]:
    return ["%s%s" % (rank, suit) for suit in SUITS for rank in RANKS]


def shuffled_deck(seed: int) -> List[str]:
    deck = full_deck()
    rng = random.Random(seed)
    rng.shuffle(deck)
    return deck


def card_rank(card: str) -> str:
    return card[0]


def card_suit(card: str) -> str:
    return card[1]


def remove_cards(deck: Iterable[str], cards_to_remove: Iterable[str]) -> List[str]:
    blocked = set(cards_to_remove)
    return [card for card in deck if card not in blocked]
