"""Bus data source (owner: B, task B5). STUB from C1.

Contract:
    get_arrivals() -> list[StopArrival]     live or replay, from cache (no I/O per message)
    mode() -> Literal["LIVE", "REPLAY"]

Stub: fixed Red-route sample arrivals, no I/O.
"""
from __future__ import annotations

from typing import Literal, Optional

from app.data import clock
from app.models import StopArrival

_forced: Optional[str] = None


def get_arrivals() -> list[StopArrival]:
    return [
        StopArrival(route_id=20, route_stop_id=268, vehicle_id=401, eta_s=240.0),
        StopArrival(route_id=20, route_stop_id=270, vehicle_id=401, eta_s=420.0),
        StopArrival(route_id=20, route_stop_id=272, vehicle_id=401, eta_s=560.0),
        StopArrival(route_id=20, route_stop_id=268, vehicle_id=402, eta_s=900.0),
        StopArrival(route_id=29, route_stop_id=301, vehicle_id=512, eta_s=360.0),
    ]


def mode() -> Literal["LIVE", "REPLAY"]:
    if _forced in ("LIVE", "REPLAY"):
        return _forced  # type: ignore[return-value]
    return clock.mode()


def force_mode(m: Optional[str]) -> None:  # used by /mode; not part of the frozen contract
    global _forced
    _forced = m.upper() if m else None
