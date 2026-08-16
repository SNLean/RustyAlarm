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

**Discord webhook**, not browser sound. The hosted service cannot play sound on the client's PC; Discord works with the PC off, on the phone. Each alarm has its own webhook. See [[Discord Webhooks]].

## Login

**Steam OpenID** (no API key). One click, and it yields the SteamID64 for free. Rust players already have Steam. See [[Steam OpenID]].

## Hosting

**Ubuntu VPS + nginx** for the domain. See [[VPS deployment]]. (Running on the owner's PC was considered and dropped — too fragile for a paid service.)

## Deliberately left as is (not bugs)

Acceptable at the "small VPS, dozens of users" scale; documented so nobody "fixes" them by accident:

- **Sync SQLite on the event loop** — sub-millisecond under WAL.
- **The runner restarts when an alarm is edited** — by design via `updated_at`.
- **A paused user can still edit their config** — they simply are not monitored.

Technical detail in [[Security review]].
