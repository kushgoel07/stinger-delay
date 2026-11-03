"""Admin commands (owner: A, task A6). STUB from C1.

handle_admin(msg) -> Optional[list[str]]: returns replies if msg is an admin command
from an allowlisted handle (ADMIN_HANDLES), else None so the message goes to the core.
Stub supports /clock, /mode, /where, /status minimally.
"""
from __future__ import annotations

import os
from typing import Optional

from app.data import clock, places, sources
from app.messaging import session
from app.models import Inbound


def _admins() -> set[str]:
    return {h.strip() for h in os.getenv("ADMIN_HANDLES", "").split(",") if h.strip()}


def handle_admin(msg: Inbound) -> Optional[list[str]]:
    text = (msg.text or "").strip()
    if not text.startswith("/") or msg.user_id not in _admins():
        return None
    cmd, _, arg = text.partition(" ")
    arg = arg.strip()
    if cmd == "/clock":
        if arg.lower() == "live":
            clock.set_live()
            return ["Clock: live."]
        day, _, hhmm = arg.partition(" ")
        try:
            clock.set_demo(day, hhmm)
        except ValueError as e:
            return [f"Clock not set: {e}"]
        return [f"Clock: {clock.now():%a %d %b %H:%M} (replay)."]
    if cmd == "/mode" and arg.lower() in ("live", "replay"):
        if arg.lower() == "live":
            clock.set_live()
        else:
            now = clock.now()
            clock.set_demo(f"{now:%a}", f"{now:%H:%M}")
        return [f"Mode: {sources.mode()}."]
    if cmd == "/where" and arg:
        hits = places.resolve(arg)
        if not hits:
            return [f"Unknown place: {arg}."]
        place = hits[0]
        session.set_location(msg.user_id, place.loc)
        return [f"Location set to {place.name}."]
    if cmd == "/status":
        from app.core import handler
        err = handler.last_error() or "none"
        return [f"Mode {sources.mode()}, clock {clock.now():%a %d %b %H:%M}, feed: stub, last error: {err}"]
    return ["Admin commands: /clock Tue 09:20 | /clock live | /mode replay|live | /where <landmark> | /status"]
