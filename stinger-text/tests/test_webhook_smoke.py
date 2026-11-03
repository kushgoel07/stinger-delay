"""C1 done-check: the app imports and a fake webhook returns a reply."""
from fastapi.testclient import TestClient

import pytest

from app.core import handler
from app.main import app


@pytest.fixture(autouse=True)
def no_grok():
    handler.set_grok(None)  # never hit the real API from tests, even if .env has a key
    yield
    handler.set_grok(None)

FAKE_TEXT = {
    "type": "new-message",
    "data": {
        "guid": "fake-guid-1",
        "text": "Can I make it to West Village by 12:15?",
        "isFromMe": False,
        "handle": {"address": "+14045550123"},
        "chats": [{"guid": "iMessage;-;+14045550123"}],
        "attachments": [],
    },
}


def test_fake_webhook_returns_reply():
    with TestClient(app) as client:
        r = client.post("/webhook/bluebubbles", json=FAKE_TEXT)
    assert r.status_code == 200
    replies = r.json()["replies"]
    assert replies and isinstance(replies[0], str) and replies[0]


def test_is_from_me_dropped():
    payload = {**FAKE_TEXT, "data": {**FAKE_TEXT["data"], "isFromMe": True}}
    with TestClient(app) as client:
        r = client.post("/webhook/bluebubbles", json=payload)
    assert r.json()["replies"] == []


def test_admin_where_unknown_place_does_not_crash(monkeypatch):
    from app.messaging import admin
    from app.models import Inbound

    monkeypatch.setenv("ADMIN_HANDLES", "+14045550100")
    out = admin.handle_admin(Inbound("+14045550100", "g", "/where hogwarts", None, None))
    assert out and out[0].startswith("Unknown place")
