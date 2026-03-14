from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SeatStatus(str, Enum):
    ACTIVE = "active"
    FOLDED = "folded"
    ALL_IN = "all_in"
    WAITING = "waiting"
    BUSTED = "busted"


class RoomStatus(str, Enum):
    LOBBY = "lobby"
    ACTIVE = "active"
    HAND_OVER = "hand_over"


class OccupantType(str, Enum):
    HUMAN = "human"
    BOT = "bot"


class Street(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    COMPLETE = "complete"


class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


class BotDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BotPersonality(str, Enum):
    ROCK = "rock"
    BALANCED = "balanced"
    LAG = "lag"
    TRICKY = "tricky"
    STATION = "station"


class OpponentModel(BaseModel):
    hands_observed: int = 0
    vpip: float = 0.18
    pfr: float = 0.12
    aggression: float = 1.0
    bluff_index: float = 0.5
    showdown_strength_mean: float = 0.5
    average_bet_ratio: float = 0.5


class BotProfile(BaseModel):
    difficulty: BotDifficulty
    personality: BotPersonality
    avatar_seed: str
    avatar_tone: str


class SeatState(BaseModel):
    seat_index: int
    occupant_id: Optional[str] = None
    occupant_name: str
    occupant_type: Optional[OccupantType] = None
    avatar_seed: str = "?"
    avatar_tone: str = "#475569"
    stack: int = 0
    status: SeatStatus = SeatStatus.WAITING
    hole_cards: List[str] = Field(default_factory=list)
    current_bet: int = 0
    total_committed: int = 0
    is_dealer: bool = False
    is_small_blind: bool = False
    is_big_blind: bool = False
    has_acted: bool = False
    bot_profile: Optional[BotProfile] = None


class PotState(BaseModel):
    amount: int
    eligible_seat_indices: List[int]


class ActionRecord(BaseModel):
    order: int
    seat_index: int
    actor_name: str
    action: ActionType
    amount: int = 0
    target_bet: int = 0
    street: Street
    note: str = ""


class HandState(BaseModel):
    hand_id: str
    hand_number: int
    street: Street
    dealer_seat: int
    small_blind_seat: int
    big_blind_seat: int
    acting_seat: Optional[int]
    board: List[str] = Field(default_factory=list)
    deck: List[str] = Field(default_factory=list)
    pot_total: int = 0
    current_bet: int = 0
    last_full_raise_size: int = 0
    min_raise_to: int = 0
    pending_to_act: List[int] = Field(default_factory=list)
    action_log: List[ActionRecord] = Field(default_factory=list)
    winner_text: str = ""
    winning_seat_indices: List[int] = Field(default_factory=list)
    revealed_hole_cards: Dict[int, List[str]] = Field(default_factory=dict)
    pots: List[PotState] = Field(default_factory=list)
    completed: bool = False


class RoomConfig(BaseModel):
    max_seats: int = Field(6, ge=2, le=6)
    bot_count: int = Field(4, ge=0, le=5)
    small_blind: int = Field(10, gt=0)
    big_blind: int = Field(20, gt=0)
    starting_stack: int = Field(2000, gt=0)
    difficulty: BotDifficulty = BotDifficulty.MEDIUM


class RoomState(BaseModel):
    room_code: str
    host_session_id: str
    status: RoomStatus = RoomStatus.LOBBY
    config: RoomConfig
    seats: List[SeatState]
    hand_state: Optional[HandState] = None
    version: int = 1
    hand_counter: int = 0
    bot_memories: Dict[str, Dict[str, OpponentModel]] = Field(default_factory=dict)
