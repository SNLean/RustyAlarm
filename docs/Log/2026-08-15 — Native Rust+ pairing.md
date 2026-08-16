---
title: Native Rust+ pairing
tags:
  - log
  - rustyalarm
  - saas
date: 2026-08-15
---

# Native Rust+ pairing (auto-fill in the wizard)

The wizard can now fill `ip`, `port`, `player_token` and `entity_id` automatically: the service registers itself as a Rust+ companion "device", the user logs in with Steam once, pairs in game, and the pairing notifications land in the wizard via polling.

## How it works

New module [[Subscription service|saas/pairing.py]], mirroring the flow of `rustplus.js` / `rustCli`:

1. `POST /api/pair/start` — registers fresh FCM credentials (Firebase Installations + GCM checkin/register3, via `push_receiver.AndroidFCM` — already a transitive dep of `rustplus` through `rustPlusPushReceiver==0.6.1`), requests an `ExponentPushToken` from Expo, and returns the Facepunch login URL with `returnUrl` → `/pair/callback`. Sets a state cookie bound to the session.
2. The user logs into `companion-rust.facepunch.com` (Steam); Facepunch redirects to `/pair/callback?token=<AuthToken>`.
3. The callback validates session + state cookie, registers our Expo token as a device of the user's account (`POST /api/push/register`, payload `AuthToken/DeviceId/PushKind:3/PushToken`) and starts an MCS listener thread (`mtalk.google.com:5228`, falling back to `443` — many networks filter 5228; the original `PushReceiver.__open` blocks with no timeout, we inject a replacement via the name-mangled instance attribute).
4. In-game pairing pushes an FCM `DataMessageStanza`; `app_data["body"]` is JSON — `type:"server"` carries ip/port/playerId/playerToken, `type:"entity"` adds entityId/entityType/entityName. The wizard polls `GET /api/pair/status` every 2 s and fills the fields (always as **strings** — big-int rule).

## Design decisions

- **All pairing state is in-memory** (PairingSession per steam_id). The Facepunch AuthToken is used once for `push/register` and discarded — never stored, never logged.
- **TTLs**: 5 min to complete the login, 10 min of listening; a global cap of 8 concurrent listeners. Closing the wizard cancels the session server-side.
- **Steam-account mismatch detection**: if the popup login used a different account than the panel session, `playerToken` would never authenticate for the alarm owner's steam_id — status returns `steam_mismatch` and the wizard warns instead of filling.
- **Stoppable listener**: `PushReceiver.listen()` reconnects forever; we drive its private `__login/__recv/__handle_ping` with a 5 s read timeout and distinguish select-timeout (quiet) from instant `None` (broken socket) by elapsed time.
- Companion app constants (Firebase api key, sender id, app id, cert, Expo project id) are public app identifiers, the same ones every community tool ships.

## Verified

- FCM + Expo registration live against Google/Expo endpoints: OK (GCM register3 needs 1–3 retries routinely).
- MCS login on the fallback port: OK (`LoginResponse` code 0); `stop()` kills the thread in ~2 s.
- Routes smoke-tested (401/403/302 paths). Full end-to-end (Steam login + in-game pair) pending a real account test.

## Follow-up — live verification (same session)

Added `saas/verify.py` + `POST /api/pair/verify` so the obtained data is **verified**, not just filled. Before the alarm is created, the wizard opens one ephemeral `RustSocket` to the paired server, calls `get_entity_info(entityId)`, and confirms the entity type is a Smart Alarm (`AppEntityType`: Switch=1, **Alarm=2**, StorageMonitor=3). This catches the `not_found` trap (Entity ID changes each wipe) up front instead of surfacing it as monitor warnings after creation.

- Error taxonomy (brief §26) → Spanish messages: `RUST_SERVER_UNREACHABLE`, `RUST_AUTH_REJECTED`, `RUST_ENTITY_NOT_FOUND`, `RUST_ENTITY_UNSUPPORTED`, `RUST_PROTOCOL_ERROR`.
- Reuses `db.is_blocked_host` (SSRF) via a shared `_validate_connection_fields` extracted from `validate_alarm`.
- In-memory per-user rate limit (single worker) so the endpoint can't be used as an on-demand port scanner.
- Soft gate: a failed verify still allows creation (server may be transiently down) but tells the user why.
- Verified live: unreachable host fails cleanly via `wait_for` (~12 s, no hang); `connect()`/`get_entity_info` bool/RustError traps handled; socket always torn down.

This applies the parts of the "Integración Steam + Rust+" technical brief that map to our stack — verification + automatic data obtaining. The rest of the brief (KMS, Redis locks, feature flags, multi-instance) is either already covered by our single-worker SQLite architecture or over-engineering for this scale; the connection worker (Manager/AlarmRunner), SSRF guard, tenant isolation, CSRF, and reconnect/backoff already existed.

## Follow-up 2 — token-delivery reality + manual fallback + SSRF hardening

Testing the automatic flow on `http://127.0.0.1:8000` hung at "waiting_login". Root cause found by reading rustplus.js's `cli/pair.html` + CLI: **Facepunch delivers the auth token via `window.ReactNativeWebView.postMessage`, not a query redirect.** The CLI catches it by launching Chrome with `--disable-web-security` and injecting a `ReactNativeWebView` shim into Facepunch's cross-origin popup — impossible for a hosted web app. What works for a hosted site is Facepunch's `?token=` **top-level redirect to a public HTTPS `returnUrl`** (how ollieee's server callback and our `/pair/callback` receive it). So:

- Automatic pairing works only with a **public HTTPS `BASE_URL`**. `/api/pair/start` now refuses on non-https and the wizard opens the manual box instead of hanging.
- Added a **manual-paste** path in the wizard (server + alarm steps): paste the pairing JSON (`ip`/`port`/`playerToken`/`playerId`, or `entityId`) and it fills the fields — works local and prod, no Facepunch return-URL dependency. Warns if the pasted `playerId` ≠ the panel's Steam account.

Adversarial review (6-dimension workflow, findings verified) surfaced real issues in the verify feature; fixed:

- **SSRF (high):** `is_blocked_host` never resolved DNS, so the new `/api/pair/verify` was an on-demand internal connect/port-scan oracle. `verify.py._safe_resolve` now resolves + rejects if any resolved IP is internal + connects to the pinned IP. Also block packed-numeric notations (`2130706433`, `0x…`, octal). The **monitor path keeps the rebind hole** (resolves at connect) — deferred.
- **Misleading verify error (medium):** a prior-wipe player token made verify say "Entity ID no existe"; now only `not_found` says that, other failures give a neutral "revisá player token y Entity ID".
- **Low:** `_verify_last` pruned so it doesn't grow per-user; `runVerify()` single-flight so a superseding 429 can't overwrite a good result.

## Follow-up 3 — the RustyAlarm Link extension (real automatic path)

Corrected an earlier wrong conclusion: HTTPS does **not** make the hosted auto-flow work. Reading rustplus.js `cli/pair.html` proved Facepunch delivers the token **only** via `window.ReactNativeWebView.postMessage` (they removed the `?token=` URL redirect), catchable only by a native app / browser extension / `--disable-web-security` browser — never a plain hosted page. The rustplus.py docs (rplus.ollieee.xyz) confirm there is **no API** to get ip/port/playerToken without FCM pairing (only `entityId` has a non-pairing path: the in-game `combatlog` trick).

So the only way to a one-click in-app flow is our own extension. Built `extension/` (MV3, Chromium):
- `inject.js` (MAIN world on Facepunch) defines the `ReactNativeWebView` bridge; `facepunch.js` relays the captured `{SteamId, Token}` to `background.js`.
- `panel.js` (on our origin) announces the extension to the panel and hands it the `link_nonce`.
- `background.js` POSTs `{nonce, token}` to `/api/pair/link`.

Backend: `/api/pair/start` now returns a single-use `link_nonce` (on the PairingSession); new `/api/pair/link` is authorized by that nonce (no cookie/`same_origin` — the extension posts cross-origin), calls `activate()` (register + listen), consumes the nonce. Removed the dead `/pair/callback` redirect route and the HTTPS gate — the extension path works on `http://127.0.0.1` too. `login_url()` dropped its `returnUrl` (unused now). The panel detects the extension via a `postMessage` handshake and only offers the auto button when present; otherwise the manual-paste box.

Reused all of `pairing.py` (FCM register + Expo + MCS listener) and `verify.py` unchanged.

## Follow-up 4 — event-loop fix, pairing-only, UX polish

- **The "No response received" bug (biggest of the session).** With pairing working, created alarms connected then showed **error** forever. Root cause: [[rustplus]] schedules `handle_message` on `get_event_loop_policy().get_event_loop()`, which under uvicorn is a non-running loop → responses never dispatch → 5 s timeout every poll. Fix: one line in `saas/app.py` lifespan — `asyncio.set_event_loop(asyncio.get_running_loop())`. A one-shot `asyncio.run` script worked, which is why it looked like flakiness. Full write-up in [[Pitfalls and fixes]] and [[rustplus]].
- **Pairing-only (manual paste removed).** Superseding follow-up 2/3: the manual-paste box is gone. The four connection fields are read-only, and `create_alarm` pulls ip/port/player_token/entity_id from the user's live pairing session server-side, ignoring the client — so crafted credentials can't be posted to the API. Editing keeps the stored credentials. See [[Product decisions]].
- **UX.** Wizard auto-advances when a step's data is detected; the extension closes the Facepunch popup after capture; the pair button hides once linked (its `.ghost` class beat the `hidden` attribute — [[Pitfalls and fixes]] #3) and the box turns green with "Cuenta vinculada".

Later in the same milestone: [[Log/2026-08-16 — Custom alarm sounds]] and the self-hosted Font Awesome pass (see [[Subscription service]]). Every error and process mistake from this milestone is catalogued in [[Pitfalls and fixes]].

## References

- [[Rust+ pairing]] — where these values come from, manual flow
- [[rustplus]] — the shared library; its `FCMListener` inspired the listener
- rustplus.js `PairingFlow.md` and `cli/index.js` — the mirrored flow
