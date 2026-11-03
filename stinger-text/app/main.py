"""StingerText FastAPI app. C wires; A and B register their routers/startup tasks here."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402

from app.data import clock, sources  # noqa: E402
from app.messaging import webhook  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # B registers the 20 s live-feed poller here (B5); cancel it after the yield.
    logging.getLogger("stingertext").info("StingerText up: mode=%s clock=%s", sources.mode(), clock.now())
    yield


app = FastAPI(title="StingerText", lifespan=lifespan)
app.include_router(webhook.router)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "mode": sources.mode(), "clock": clock.now().isoformat()}
