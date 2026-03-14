from __future__ import annotations

from pydantic import BaseModel


class OpponentModel(BaseModel):
    opponent_id: str
    vpip: float = 0.22
    pfr: float = 0.14
    aggression_factor: float = 1.0
    bluff_index: float = 0.5
