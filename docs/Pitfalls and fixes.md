---
title: Pitfalls and fixes
tags:
  - reference
  - lessons
  - rustyalarm
date: 2026-08-16
---

# Pitfalls and fixes

Concrete bugs and process mistakes hit while building native pairing, live verification and custom sounds — with the root cause and the fix, so we don't repeat them. Newest first. Code-level traps also live in [[rustplus]]; this page is the narrative "what bit us and why".

---

## 1. Alarms stuck on "No response received" under uvicorn (the big one)

**Symptom.** An alarm connected fine ("Conectado a Rust+"), then every poll returned `RustError("No response received")` and the card showed **error** forever. A one-shot script (`asyncio.run`) against the same server worked, so it looked like flakiness. `stdout` spammed `run_proto_event was never awaited`.

**Root cause.** [[rustplus]] schedules its socket read-handlers with `asyncio.get_event_loop_policy().get_event_loop().create_task(...)` — including `handle_message`, which matches responses to requests. Under uvicorn that resolves to a **non-running** event loop, so `handle_message` never executes → `send_and_get` times out after 5 s → `get_entity_info` returns the error. The one-shot worked because `asyncio.run()` sets the thread's loop, so the policy loop *was* the running loop.

**Fix.** Pin the policy loop to the running loop at startup, in `saas/app.py` lifespan:
```python
asyncio.set_event_loop(asyncio.get_running_loop())
```
Do not remove that line. The desktop tool never needed it (`asyncio.run()` in its thread already sets the loop).

**Lesson.** When a library uses `get_event_loop()`/`get_event_loop_policy().get_event_loop()` instead of `get_running_loop()`, it can silently target the wrong loop under an ASGI server. "Connects but never gets a response," where a standalone script works, is the fingerprint. Diagnose by reproducing the *sustained* session, not a one-shot.

## 2. Facepunch delivers the pairing token by postMessage, not a redirect

**Mistake.** First conclusion was that the automatic hosted flow would work once `BASE_URL` was public **HTTPS**, via a `?token=` redirect to `/pair/callback`. Wrong — and stated too confidently.

**Reality (verified in `rustplus.js` `cli/pair.html` + the rustplus.py docs, and re-checked by an adversarial workflow).** After Steam login, Facepunch calls `window.ReactNativeWebView.postMessage({SteamId, Token})`. It **no longer** puts the token in any redirect URL (query or fragment). Only the mobile app, a browser **extension**, or a `--disable-web-security` browser can define that bridge and read the token. A plain hosted page cannot inject into the cross-origin popup. `companion-rust.facepunch.com/app?returnUrl=` returns HTTP 500 and carries no token; `/login?returnUrl=` only controls post-login navigation to an internal path.

**Fix.** Ship our own MV3 extension (`extension/`, "RustyAlarm Link") that defines the bridge, captures the token, and POSTs it to `/api/pair/link` with a single-use `link_nonce`. This works on any origin, localhost included — it does **not** depend on Facepunch redirecting to us. See [[Rust+ pairing]] and [[Log/2026-08-15 — Native Rust+ pairing]].

**Lesson.** Verify the token-delivery mechanism from primary sources (the actual capture code) before designing around it. There is **no** extension-free path for a hosted web app, and no public API shortcut (the rustplus.py docs confirm FCM pairing is the only way to get ip/port/playerToken; only `entityId` has the in-game `combatlog` shortcut). Don't over-state a hypothesis as a conclusion.

## 3. `hidden` attribute didn't hide the pair button

**Symptom.** After pairing succeeded, the "Vincular con Rust+" button stayed visible, reading as "stuck on this step."

**Root cause.** The button carries the `.ghost` class which sets an explicit `display`. A class selector beats the user-agent `[hidden] { display: none }` rule, so setting the `hidden` attribute did nothing.

**Fix.** Toggle visibility with `element.style.display` (or a dedicated class), not the `hidden` attribute, when the element already has a `display` from CSS. Also made the linked state affirmative (green border + "Cuenta vinculada") so it reads as progress.

**Lesson.** `[hidden]` is trivially overridden by any rule that sets `display`. For elements styled by class, hide via inline style or a `.is-hidden { display:none !important }` helper.

## 4. SSRF via DNS + packed-numeric IPs in `is_blocked_host`

**Found by** the adversarial review of the live-verify feature.

**Root cause.** `db.is_blocked_host()` never resolved DNS, so a public hostname whose A record points at an internal IP passed it; and packed-numeric notations (`2130706433`, `0x7f000001`, octal `0177.0.0.1`) that `ipaddress` won't parse fell through to the "it's a hostname" branch, yet glibc `getaddrinfo` expands them to loopback. The new `/api/pair/verify` (an on-demand outbound connect) turned this into an internal-network connect/port-scan oracle.

**Fix.** `verify.py._safe_resolve()` resolves the host, rejects if **any** resolved address is internal, and connects to the **pinned** IP (no rebind between check and connect). `is_blocked_host` now also blocks the packed-numeric forms. The monitor path still resolves at connect time (documented, deferred) — resolve+pin+recheck there too if touched. See [[Security review]].

**Lesson.** An SSRF allowlist/denylist that doesn't resolve DNS is bypassable; resolve, check every returned address, and pin the IP you actually connect to.

## 5. verify misreported a bad player token as "Entity ID doesn't exist"

**Root cause.** On a prior-wipe player token the server silently drops the request → `get_entity_info` returns `RustError("No response received")`. The code matched reason substrings that Rust+ never sends and fell through to the `RUST_ENTITY_NOT_FOUND` message, telling the user to fix the Entity ID when the real problem was the token.

**Fix.** Only say "entity doesn't exist" when the reason literally contains `not_found`; for anything else give a neutral message that names both likely causes (player token / Entity ID). Never treat `connect()==True` as proof the credentials authenticate.

**Lesson.** Don't infer a specific cause from a generic/absent error. Map only what the upstream explicitly says; be neutral otherwise.

## 6. Sound upload buffered the whole file before the size check

**Found by** the adversarial review of the sounds feature (low severity — admin-only).

**Root cause.** `admin_upload_sound` did `await upload.read()` and checked `len(data) > MAX_BYTES` **after** the whole file was in memory; Starlette had already spooled the multipart part with no size cap. A large upload could exhaust the single worker's memory.

**Fix.** Reject by `Content-Length` and `UploadFile.size` **before** materializing the body.

**Lesson.** Enforce upload limits before reading the body, not after. On a single-worker process an OOM takes down every user's monitoring, so "admin-only" doesn't make it free.

## 7. CSP blocks CDNs — self-host everything

**Symptom.** Font Awesome from a CDN would silently not load.

**Root cause.** The middleware CSP is strict: `default-src 'self'`, no `media-src`/`font-src` override. External CSS, fonts, scripts and icon kits are blocked.

**Fix.** Self-host Font Awesome Free (solid) under `saas/static/fa/`, mounted at `/static`; link it from `base.html`. `style-src 'self'` allows the `<link>`; `font-src` falls back to `default-src 'self'` for the woff2. Use `<i class="fas fa-…">`; never a CDN. Note: an icon put into a `textContent` assignment renders as literal text — switch to `innerHTML` with a static string or drop the glyph.

**Lesson.** Under this CSP, any new external asset must be vendored into `/static`. Check the CSP before adding a dependency that loads from a URL.

## 8. PROCESS: never test DB writes against the live database

**What happened.** A quick test to verify the pairing-only enforcement ran against the real `saas_data/rustalarm.db`, and its "clear alarms to count cleanly" step **deleted the user's real alarm**. Its Rust+ credentials were unrecoverable (pairing data, not in git or `.history/`).

**Fix / rule.** Set `RUSTALARM_DATA_DIR` to a scratch dir **before** importing `saas.*` in any test or diagnostic that writes. Read-only diagnostics may touch the live DB but must never DELETE/UPDATE/INSERT. This is also saved as an agent memory.

**Lesson.** Treat `saas_data/` as production. The default `config.DB_PATH` points at the live DB; a throwaway test must never inherit it.

---

## Quick checklist before shipping SaaS changes

- [ ] New library uses `get_running_loop()` where it schedules tasks? If not, watch for loop-mismatch under uvicorn (pitfall 1).
- [ ] New external asset (font/script/icon/style)? Self-host under `/static` (pitfall 7).
- [ ] New outbound connect from user input? Resolve + pin + re-check for SSRF (pitfall 4).
- [ ] New upload? Enforce size before buffering (pitfall 6).
- [ ] Any DB-writing test? `RUSTALARM_DATA_DIR` = scratch dir first (pitfall 8).
- [ ] Toggling visibility on a class-styled element? Use `style.display`, not `[hidden]` (pitfall 3).
