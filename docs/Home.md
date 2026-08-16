---
title: RustyAlarm — Index
tags:
  - moc
  - rustyalarm
aliases:
  - Home
  - MOC
  - Index
---

# RustyAlarm 🔔

A service that watches a Rust (the game) **Smart Alarm** through the Rust+ API and alerts you when it fires. Two products in one repo, sharing the [[rustplus]] library.

> [!info] Documentation language
> This vault is written in **English** (it is internal/agent documentation — better for tooling). Everything the **end user** sees — the templates, the wizard, error messages, the landing — stays in **Spanish**. See [[Maintaining this vault]].

> [!info] Repository
> Private: [github.com/SNLean/RustyAlarm](https://github.com/SNLean/RustyAlarm) · branch `main`

## Map

- [[Architecture]] — how everything fits together
- [[Subscription service]] — the multi-user web app (`saas/`)
- [[Desktop tool]] — the original local app (`webapp.py`, `rust.py`)
- [[Product decisions]] — what was chosen and why
- [[Security review]] — findings from the adversarial review and their fixes
- [[VPS deployment]] — Ubuntu + nginx + HTTPS

## References (official docs)

- [[rustplus]] — the Rust+ Python library
- [[Rust+ pairing]] — where Steam ID, player token and entity ID come from
- [[Steam OpenID]] — Steam login
- [[FastAPI and Uvicorn]] — the service stack
- [[nginx and systemd]] — running in production
- [[Discord Webhooks]] — the alert channel
- [[Design and animation skills]] — tooling to polish UI/motion

## Session log

- [[Log/2026-08-15 — From script to service]]
- [[Log/2026-08-15 — Design and animation skills]]
- [[Log/2026-08-15 — Guided alarm wizard]]
- [[Log/2026-08-15 — Frontend redesign]]
- [[Log/2026-08-15 — README and official docs]]
- [[Log/2026-08-15 — Security audit and fixes]]
- [[Log/2026-08-15 — Native Rust+ pairing]]

## Meta

- [[Maintaining this vault]]
