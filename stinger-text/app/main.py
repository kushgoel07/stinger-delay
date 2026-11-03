"""StingerText FastAPI app. C wires; A and B register their routers/startup tasks here."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402

from app.api import router as data_router  # noqa: E402
from app.data import clock, sources  # noqa: E402
from app.messaging import webhook  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # B's live-feed poller starts lazily on the first LIVE get_arrivals(); stop it on shutdown.
    logging.getLogger("stingertext").info("StingerText up: mode=%s clock=%s", sources.mode(), clock.now())
    yield
    sources.stop_poller()


app = FastAPI(title="StingerText", lifespan=lifespan)
app.include_router(webhook.router)
app.include_router(data_router)


@app.get("/")
def root() -> dict:
    return {"service": "stinger-text", "mode": sources.mode(), "now": clock.now().isoformat()}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "mode": sources.mode(), "clock": clock.now().isoformat()}
