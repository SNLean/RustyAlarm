---
title: 2026-08-15 — Guided alarm wizard
tags:
  - log
  - session
  - ui
date: 2026-08-15
---

# 2026-08-15 — Guided alarm wizard

Alarm creation went from a dense single form to a **guided, interactive step-by-step wizard**, because a new user could not tell where the four pairing values came from. See [[Subscription service]].

## What was done

1. **7-step wizard** in `saas/templates/panel.html`: Welcome (first alarm only) → Name → Server → Alarm → Discord → Settings → Summary. Progress bar, per-step validation, step transition, `Back`/`Next`.
2. **Onboarding** on the first alarm: explains the 3 steps and the requirements before asking for data.
3. **In-app guides** as collapsible `<details>` on each step: how to pair the server ([[Rust+ pairing]]), how to get the entity ID, how to create the webhook. Without leaving the page.
4. **Test the webhook before saving**: new endpoint `POST /api/webhook/test` (`saas/app.py`) + `db.is_discord_webhook()`. Sends a test embed to a loose URL.
5. **Summary** at the end with everything entered (flags "no webhook — no alert" if left empty) and states that after creating, the alarm is active and monitored 24/7.
6. Edit mode reuses the wizard without the welcome step, pre-filled.

## Verification

- HTTP: the panel renders the 7 steps, 3 guides, test button; the endpoint validates the webhook (invalid/empty → 400); full create via the final-submit path → 200.
- Browser: walk-through Welcome → … → Summary → Create; per-step validation (empty name blocks); collapsible guide; card created OK; edit without welcome and pre-filled. No console errors.

## Alignment fix

Content jumped between steps: horizontal (scrollbar appearing/disappearing by step length) and vertical (the dialog resizing). Fix in `.wiz-body`: `scrollbar-gutter: stable` (always reserves the scrollbar gap) + `height: clamp(300px, 54vh, 460px)` (fixed height). Verified: identical left edge (387px) and constant body height (389px) between a non-scrolling and a scrolling step.

A second offset: in the IP / Port row, IP had no help line and Port did, so the port input sat lower. Fix: `.frow .field` as flex column with `input { margin-top: auto }` (inputs pin to the bottom and align even when one column has more help) + a one-line help added to IP. Verified: both inputs share top and bottom (324 / 369).

## Note

A real Steam login remained in the DB during testing (`76561198383652437`); it is a legitimate account, not deleted.

## Sources

- [MDN — &lt;dialog&gt;](https://developer.mozilla.org/docs/Web/HTML/Element/dialog)
- [MDN — &lt;details&gt;](https://developer.mozilla.org/docs/Web/HTML/Element/details)
- [Discord — Execute Webhook](https://discord.com/developers/docs/resources/webhook#execute-webhook)
