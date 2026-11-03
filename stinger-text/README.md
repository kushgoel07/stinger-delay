# StingerText

iMessage bot that answers "Can I make it to <place> on the Stinger?" for Georgia Tech riders.
FastAPI app; BlueBubbles webhooks in, xAI Grok for language, plain Python for all time math.
See the PRD for the full spec. Recorded bus data is read from this repo's
`Platform/` and `Analysis/` CSVs (as data only; no code is copied from them).

## Run

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env              # fill in XAI_API_KEY etc.
.venv/bin/uvicorn app.main:app --port 8000
.venv/bin/pytest -q
.venv/bin/python scripts/check_grok.py       # pre-event: one live Round-1 call
.venv/bin/python scripts/eval_utterances.py  # C4: 20-phrasing Round-1 eval (needs a real key)
```

Without `XAI_API_KEY` the app still answers: a local keyword parser stands in for Round 1
and a deterministic template stands in for Round 2.

## Ownership

| Folder | Owner | State |
|---|---|---|
| `app/models.py` | C | Frozen contracts (version on main, with B's `audio_path` on `Inbound`) |
| `app/core/` (handler, grok, prompts, fallback) | C | Real |
| `app/messaging/` (webhook, bluebubbles, location, session, admin) | A | **Stubs from C1** |
| `app/data/` (clock, sources, places, stops/segments/slip data) and `app/api.py` | B | Real |
| `app/routing/` (router, params) | B | Real |

### Stubs for A to replace

- `app/messaging/*` are minimal. The webhook stub runs synchronously and returns the replies in the response body. A2 must answer 200 within 100 ms and process the message in a background task.

## Contract decisions (C to A and B)

1. **A sends the ack, not the handler.** `handler.handle()` blocks on Grok for up to about 6 s, so it cannot get anything out within 1 s. A's webhook sends `handler.ACK_TEXT` ("Checking buses...") right after accepting a message, then calls `handle()` in the background task. Suggested rule: ack every non-admin message that has text, and skip the ack for a location-only message, whose reply is instant. `handle()` never returns the ack.
2. **The handler appends the mode footer** (`[LIVE]` or `[REPLAY Tue 3 Mar 12:00]`) to every reply it returns, prompts and clarifications included. A must not add another footer. The only reply without one is the error text ("Something went wrong on my end. Try again in a moment."), so a broken clock cannot break the error path.
3. **Admin commands are parsed by A before `handle()`** is called. `/status` reads `handler.last_error()`.
4. **`session.set_pending(user_id, None)` clears** the pending question. `get_pending` does not clear it.
5. **Pending follow-ups:** when a question is pending and the user then texts a landmark ("I'm at the CRC"), the handler sends Grok both texts together, so the original destination and deadline are kept.
6. **`TripOption.wait_s`:** B's router sets it to the time spent at the stop after walking there (`board_eta - walk_to_stop_s`). The handler reports the bus ETA from now as `walk_to_stop_s + wait_s` ("Red bus in 7 min"). Walk-only minutes are computed as `walk.arrive_at - plan.now`, so they don't depend on how B splits the walk fields.
7. **Footer date:** the footer is formatted from `TripPlan.now` (or `clock.now()` when there is no plan). With B's clock on main this prints `[REPLAY Tue 3 Mar 12:00]` at startup.
8. **Off-topic:** if Grok makes no tool call, the handler sends a fixed one-line decline. Grok's own text is never forwarded, which shuts out prompt injection.
9. **Grok never does arithmetic:** Round 2 gets a digest of the TripPlan with minutes and HH:MM already computed (`fallback.plan_facts`). A Grok reply that is over 320 characters, or that mentions a time or minute count not in that digest, is thrown away and the template is used.
10. **UNKNOWN origin** ("I'm at Hogwarts") stores the question as pending and asks the user to name a building or drop a pin. **UNKNOWN destination** gets one clarifying question naming the 3 closest gazetteer matches: `places.resolve` hits first, topped up by similarity ranking, since `resolve` only returns confident matches.
11. **Pins more than 3 km from campus center** are handled by the handler, which asks the user to drop a new pin or name a building. `/where` is admin-only, so ordinary users aren't pointed to it.
12. **Model:** `GROK_MODEL=grok-4.3` with `GROK_REASONING_EFFORT=none` (grok-4-fast-non-reasoning was retired 15 May 2026). `reasoning_effort` is sent only when it's set. If the API rejects it, the request is retried once without it and the parameter stays off for the rest of the run.

## Shared rules

All times come from `clock.now()`. Nothing outside `app/data/clock.py` reads wall time.
Session TTLs use `time.monotonic()`, which is elapsed time and not a clock reading.

## Data and routing (B)

Replay-first planner for Red (20), Green (17), and Gold (29). Clough (28) is excluded. App time comes from `app.data.clock.now()`.

Startup is replay at Tuesday 12:00 America/New_York. Each route uses the recorded snapshot `clock.replay_frame` selects (same weekday when that minute is covered, otherwise another weekday, never more than 60 seconds stale).

### Tests

```bash
cd stinger-text
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

Run from `stinger-text/` so `app` imports. Klaus → West Village at the default Tuesday noon replay returns a `TripPlan`. The fixed pairs covered by the router tests are Klaus → West Village, West Village → Klaus, Kendeda → West Village, Klaus → North Ave, and CULC → Clough, plus Howey → Bobby Dodd, Skiles → Kendeda, and Student Center → MARTA.

Origins within 250 m are walk-only. If no bus can be caught, the plan says so on `notes`. Origins more than 3 km from campus center still return a plan and ask the caller to confirm the location.

### Verdicts

With a deadline, slack is `deadline - (arrival + slip_buffer_s)`. `MAKE_IT` means slack is at least 180 seconds. `TIGHT` means slack is inside ±180 seconds. Otherwise the verdict is `WONT_MAKE_IT`. No deadline yields `NO_DEADLINE`. Slip changes the verdict only. It does not change `arrive_at`.

### Ride time

Red ride time is the next-stop ETA plus median segment seconds from board to alight.

Green and Gold ride time is `ETA(alight) - ETA(board)` when both ETAs are on the same vehicle and the alight ETA is later. A vehicle with one ETA, equal ETAs, an earlier alight ETA, or only the other vehicle's ETA is not a ride, and segment medians do not fill that gap. The plan walks.

### Live feed

`BUS_FEED_HOST` defaults to `bus.gatech.edu` (same public map as `gatech.transloc.com`). The key and host live in `.env.example` (`BUS_FEED_KEY`). The poller calls `GetRouteStopArrivals` every 20 seconds on a background thread. `get_arrivals()` only reads that cache.

Three consecutive failures in one live session call `clock.set_demo` for the current weekday and minute. A successful poll starts a fresh streak. `set_live` and `set_demo` start a fresh streak too, so returning to live does not inherit the old count.

### Fixture

Probed Mon 2 Nov 2026. `GetMapStopPoints` timed out, so stop names and coordinates are in `stops.json`. One `GetRouteStopArrivals` body is saved at `fixtures/feed_arrivals.json`: 63 stop entries, Red 20 (18), Gold 29 (21), Blue 21 (13), and Clough 28 (11). Green 17 was not running. The parser keeps Red and Gold and drops Blue and Clough.
