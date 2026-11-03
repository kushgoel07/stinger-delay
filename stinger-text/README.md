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
| `app/data/` clock, places, places.json, stops/segments/slip data | B | Real (B4, B7, B2, B3) |
| `app/data/sources.py` | B | **Stub from C1** |
| `app/routing/` (router, params) | B | router is a **stub**; params has the PRD constants |

### Stubs for A and B to replace

- `app/data/sources.py` returns fixed Red arrivals; B5 adds the live poller and the replay frame. `force_mode()` is a stub helper for `/mode`, not part of the contract.
- `app/routing/router.py` builds a plausible but fake plan from six hard-coded Red stops with a fixed 4-minute wait.
- `app/messaging/*` are minimal. The webhook stub runs synchronously and returns the replies in the response body. A2 must answer 200 within 100 ms and process the message in a background task.

## Contract decisions (C to A and B)

1. **A sends the ack, not the handler.** `handler.handle()` blocks on Grok for up to about 6 s, so it cannot get anything out within 1 s. A's webhook sends `handler.ACK_TEXT` ("Checking buses...") right after accepting a message, then calls `handle()` in the background task. Suggested rule: ack every non-admin message that has text, and skip the ack for a location-only message, whose reply is instant. `handle()` never returns the ack.
2. **The handler appends the mode footer** (`[LIVE]` or `[REPLAY Tue 3 Mar 12:00]`) to every reply it returns, prompts and clarifications included. A must not add another footer. The only reply without one is the error text ("Something went wrong on my end. Try again in a moment."), so a broken clock cannot break the error path.
3. **Admin commands are parsed by A before `handle()`** is called. `/status` reads `handler.last_error()`.
4. **`session.set_pending(user_id, None)` clears** the pending question. `get_pending` does not clear it.
5. **Pending follow-ups:** when a question is pending and the user then texts a landmark ("I'm at the CRC"), the handler sends Grok both texts together, so the original destination and deadline are kept.
6. **`TripOption.wait_s` (needs B to confirm):** the handler treats it as the bus's ETA at the boarding stop counted from `now` ("Red bus in 4 min"), not the time spent standing at the stop. Walk-only minutes are computed as `walk.arrive_at - plan.now`, so they don't depend on how B splits the walk fields.
7. **Footer date:** the footer is formatted from `TripPlan.now` (or `clock.now()` when there is no plan). With B's clock on main this prints `[REPLAY Tue 3 Mar 12:00]` at startup.
8. **Off-topic:** if Grok makes no tool call, the handler sends a fixed one-line decline. Grok's own text is never forwarded, which shuts out prompt injection.
9. **Grok never does arithmetic:** Round 2 gets a digest of the TripPlan with minutes and HH:MM already computed (`fallback.plan_facts`). A Grok reply that is over 320 characters, or that mentions a time or minute count not in that digest, is thrown away and the template is used.
10. **UNKNOWN origin** ("I'm at Hogwarts") stores the question as pending and asks the user to name a building or drop a pin. **UNKNOWN destination** gets one clarifying question naming the 3 closest gazetteer matches: `places.resolve` hits first, topped up by similarity ranking, since `resolve` only returns confident matches.
11. **Pins more than 3 km from campus center** are handled by the handler, which asks the user to drop a new pin or name a building. `/where` is admin-only, so ordinary users aren't pointed to it.
12. **Model:** `GROK_MODEL=grok-4.3` with `GROK_REASONING_EFFORT=none` (grok-4-fast-non-reasoning was retired 15 May 2026). `reasoning_effort` is sent only when it's set. If the API rejects it, the request is retried once without it and the parameter stays off for the rest of the run.

## Shared rules

All times come from `clock.now()`. Nothing outside `app/data/clock.py` reads wall time.
Session TTLs use `time.monotonic()`, which is elapsed time and not a clock reading.
