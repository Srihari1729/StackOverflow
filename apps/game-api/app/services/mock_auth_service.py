from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SessionRecord:
    session_id: str
    display_name: str


class MockAuthService:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionRecord] = {}

    def create_session(self, display_name: str) -> SessionRecord:
        record = SessionRecord(session_id=f"session_{uuid.uuid4().hex[:12]}", display_name=display_name)
        self._sessions[record.session_id] = record
        return record

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        return self._sessions.get(session_id)
