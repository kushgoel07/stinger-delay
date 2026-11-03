"""Minimal webhook sink: saves raw BlueBubbles events to fixtures/raw/. Never prints message text."""
import json
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request

RAW = Path(__file__).resolve().parent.parent / "fixtures" / "raw"
app = FastAPI()


@app.post("/webhook/bluebubbles")
async def webhook(request: Request) -> dict:
    body = await request.json()
    etype = str(body.get("type", "unknown")) if isinstance(body, dict) else "unknown"
    safe = "".join(ch for ch in etype if ch.isalnum() or ch in "-_")
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{int(time.time())}_{safe}.json").write_text(json.dumps(body, indent=2))
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        data = {}
    chats = data.get("chats") or [{}]
    chat_guid = str(chats[0].get("guid", ""))
    kind = "group" if ";+;" in chat_guid else "dm"
    names = [a.get("transferName") for a in data.get("attachments") or []]
    print(f"{etype} isFromMe={data.get('isFromMe')} {kind} attachments={len(names)} {names}", flush=True)
    return {"ok": True}


if __name__ == "__main__":
    # access_log off: the request line would include ?password=...
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False, log_level="warning")
