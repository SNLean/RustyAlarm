---
title: Product decisions
tags:
  - decisions
  - rustyalarm
date: 2026-08-15
---

# Product decisions

Owner's choices (2026-08-15) that are not derivable from the code. History in [[Log/2026-08-15 — From script to service]].

## Billing

> [!note] No payments yet
> `users.plan_active` is toggled by hand from `/admin`. Payment-provider integration is deferred until the product is validated. When added, that provider drives the `plan_active` flag.

## Alert channel

**Discord webhook is the reliable channel.** It works with the PC off, on the phone — the backend fires it whether or not anyone has the panel open. Each alarm has its own webhook. See [[Discord Webhooks]].

> [!note] Browser sound is an *addition*, not the channel (updated 2026-08-16)
> Alarms can now also play a **custom sound in the panel** when they fire — but only while the page is open, and it never replaces Discord. Playback is frontend-only (the monitor is untouched); the owner grows a sound catalog from `/admin`. This does not contradict "Discord, not browser sound" as the *primary* channel — it layers a convenience on top for users watching the panel. See [[Subscription service]].

## Login

**Steam OpenID** (no API key). One click, and it yields the SteamID64 for free. Rust players already have Steam. See [[Steam OpenID]].

## Pairing (added 2026-08-16)

> [!note] Data comes only from a real Rust+ pairing — no manual entry
> The connection fields (ip/port/player_token/entity_id) can't be typed or pasted; they're filled by pairing and enforced server-side. This prevents users pointing the monitor at arbitrary hosts and ties the data to their own Steam account. The trade-off: pairing needs our browser **extension** (Facepunch hands the token through a native bridge no website can read — see [[Rust+ pairing]]). Chosen deliberately over a manual-paste fallback for safety and a cleaner flow.

## Hosting

**Ubuntu VPS + nginx** for the domain. See [[VPS deployment]]. (Running on the owner's PC was considered and dropped — too fragile for a paid service.)

## Deliberately left as is (not bugs)

Acceptable at the "small VPS, dozens of users" scale; documented so nobody "fixes" them by accident:

- **Sync SQLite on the event loop** — sub-millisecond under WAL.
- **The runner restarts when an alarm is edited** — by design via `updated_at`.
- **A paused user can still edit their config** — they simply are not monitored.

Technical detail in [[Security review]].
