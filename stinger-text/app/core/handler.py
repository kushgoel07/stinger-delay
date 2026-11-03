"""Core handler (owner: C). C1 STUB: canned reply. Replaced in C3."""
from __future__ import annotations

from typing import Optional

from app.models import Inbound

ACK_TEXT = "Checking buses..."


def handle(msg: Inbound) -> list[str]:
    return ["TIGHT. Walk 2 min to Ferst Dr stop, Red bus in 4 min, arrive West Village 12:08. "
            "Walking takes 19 min. [REPLAY Tue 3 Mar 12:00]"]


def last_error() -> Optional[str]:
    return None
