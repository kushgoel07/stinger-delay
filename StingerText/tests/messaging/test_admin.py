import pytest

from app.data import clock, places, sources
from app.messaging import admin, replies, session
from app.models import LatLng

ADMIN = "+15550001111"


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list:
    session.reset_all()
    monkeypatch.setenv("ADMIN_HANDLES", f"{ADMIN}, Boss@Example.com")
    rec: list = []
    monkeypatch.setattr(clock, "set_demo", lambda d, t: rec.append(("demo", d, t)))
    monkeypatch.setattr(clock, "set_live", lambda: rec.append(("live",)))
    monkeypatch.setattr(sources, "set_mode", lambda m: rec.append(("mode", m)))
    yield rec
    session.reset_all()


def test_clock_set(calls):
    assert admin.run(ADMIN, "/clock tue 09:20") == ["Clock set to Tue 09:20. Mode: REPLAY."]
    assert calls == [("demo", "Tue", "09:20"), ("mode", "replay")]


def test_clock_bad(calls):
    assert admin.run(ADMIN, "/clock Funday 25:99") == [admin.CLOCK_USAGE]
    assert calls == []


def test_live_and_mode(calls):
    assert admin.run(ADMIN, "/clock live") == ["Clock is live. Mode: LIVE."]
    assert admin.run(ADMIN, "/mode live") == ["Mode: LIVE."]
    assert admin.run(ADMIN, "/mode replay") == ["Mode: REPLAY."]
    assert calls == [("live",), ("mode", "live"), ("mode", "live"), ("mode", "replay")]


def test_where(calls):
    assert admin.run(ADMIN, "/where klaus") == ["Location set to Klaus Advanced Computing Building."]
    assert session.get_location(ADMIN) == LatLng(33.7772, -84.3956)
    assert admin.run(ADMIN, "/where nowhere") == ['No match for "nowhere".']
    assert session.get_location("boss@example.com") is None


def test_status(calls, monkeypatch):
    from datetime import datetime
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 3, 3, 9, 20))
    monkeypatch.setattr(sources, "status", lambda: {"mode": "REPLAY", "feed_ok": False})
    monkeypatch.setattr(replies, "LAST_ERROR", None)
    assert admin.run(ADMIN, "/status") == ["Mode: REPLAY. Clock: Tue 3 Mar 09:20. Feed OK: no. Last error: none."]


def test_non_admin_and_other(calls):
    assert admin.run("+15559999999", "/clock Tue 09:20") == []
    assert calls == []
    assert admin.run("boss@example.com", "/foo") == [admin.HELP]
    assert admin.is_command(" /x") and not admin.is_command("hi") and not admin.is_command(None)
