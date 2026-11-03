"""Router (owner: B, task B6). STUB from C1.

Contract:
    plan_trip(origin: LatLng, dest: Place, deadline: Optional[datetime]) -> TripPlan

Stub: plausible but FAKE plan from a handful of hard-coded Red stops with a fixed
4-minute wait. No I/O. B6a/B6b replace it with the real algorithm.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional

from app.data import clock, sources
from app.models import LatLng, Place, Stop, TripOption, TripPlan
from app.routing import params

# Placeholder Red (20) stops, loop order. Names/coords are illustrative only.
_STUB_STOPS = [
    Stop(268, 20, "Ferst Dr at Klaus", LatLng(33.7775, -84.3956), 1),
    Stop(270, 20, "Ferst Dr at Student Center", LatLng(33.7735, -84.3985), 2),
    Stop(272, 20, "Ferst Dr at CRC", LatLng(33.7754, -84.4030), 3),
    Stop(274, 20, "West Village", LatLng(33.7793, -84.4045), 4),
    Stop(276, 20, "Tech Square", LatLng(33.7770, -84.3895), 5),
    Stop(278, 20, "North Ave Apts", LatLng(33.7712, -84.3918), 6),
]


def haversine_m(a: LatLng, b: LatLng) -> float:
    r = 6371000.0
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp, dl = p2 - p1, math.radians(b.lng - a.lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def walk_s(a: LatLng, b: LatLng) -> float:
    return haversine_m(a, b) * params.DETOUR / params.WALK_MPS


def _verdict(arrive: datetime, buffer_s: float, deadline: Optional[datetime]) -> str:
    if deadline is None:
        return "NO_DEADLINE"
    margin = (deadline - (arrive + timedelta(seconds=buffer_s))).total_seconds()
    if margin >= params.TIGHT_WINDOW_S:
        return "MAKE_IT"
    if margin >= -params.TIGHT_WINDOW_S:
        return "TIGHT"
    return "WONT_MAKE_IT"


def plan_trip(origin: LatLng, dest: Place, deadline: Optional[datetime]) -> TripPlan:
    now = clock.now()
    w = walk_s(origin, dest.loc)
    walk = TripOption("walk", None, None, None, None, 0.0, 0.0, 0.0, w,
                      now + timedelta(seconds=w), "unknown", 0.0)
    options = [walk]
    if haversine_m(origin, dest.loc) >= params.WALK_ONLY_UNDER_M:
        board = min(_STUB_STOPS, key=lambda s: haversine_m(origin, s.loc))
        alight = min(_STUB_STOPS, key=lambda s: haversine_m(dest.loc, s.loc))
        if board is not alight:
            to_s = walk_s(origin, board.loc)
            wait = max(240.0, to_s + params.CATCH_MARGIN_S)
            hops = (alight.seq - board.seq) % len(_STUB_STOPS)
            ride = hops * 75.0
            from_s = walk_s(alight.loc, dest.loc)
            arrive = now + timedelta(seconds=wait + ride + from_s)
            options.append(TripOption("bus", 20, "Red", board, alight, to_s, wait, ride, from_s,
                                      arrive, "slightly_late", 90.0))
    options.sort(key=lambda o: o.arrive_at)
    best = options[0]
    return TripPlan(origin=origin, dest=dest, now=now, deadline=deadline, best=best, walk=walk,
                    alternatives=options[1:3], verdict=_verdict(best.arrive_at, best.slip_buffer_s, deadline),
                    mode=sources.mode())
