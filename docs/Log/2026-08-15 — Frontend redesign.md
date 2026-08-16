---
title: 2026-08-15 — Frontend redesign
tags:
  - log
  - session
  - ui
  - design
date: 2026-08-15
---

# 2026-08-15 — Frontend redesign

Full redesign of the [[Subscription service]] front using three skills: `frontend-design` (Anthropic), `emil-design-eng` and `animate`. See [[Design and animation skills]].

## Direction

Elevate the current identity (dark + Rust orange) to premium. Concept: it is a **monitoring/surveillance** service, so the signature is a **live signal** ("we are watching 24/7") present in header, hero and cards. Everything else stays disciplined.

## Design decisions

- **Token system** in `base.html`: layered warm-dark surfaces, refined Rust vermilion (`#db4325`) + signal green, radius/shadow scales, motion tokens (strong `--ease-out`, durations <300ms). Old names kept as aliases (`--panel`, `--accent`, `--ok`…) so existing CSS does not break.
- **Typography**: system sans for text; **monospace for all telemetry** (IP, entity IDs, status, timestamps, eyebrows, progress). Technical-console character without external fonts — the CSP blocks them (`font-src` falls back to `'self'`).
- **Landing**: two-column hero with a **monitoring console** as the signature (server + ONLINE signal + SONANDO alarm + Discord delivery); "how it works" in 3 real steps (it is a sequence); features in user language; staggered scroll reveals.
- **Panel**: elevated cards with a rust glow when `alarm_on` (`.fired`), status pills with a per-color signal dot (green/amber/rust), mono telemetry. The wizard keeps its structure and alignment fixes.
- **Admin**: refined table, status as a pill, mono ids/dates.

## Motion (emil / animate)

- Buttons: `:active { scale(.97) }`, `transform` transition 130ms `ease-out`.
- Reveal on scroll once (IntersectionObserver → `.is-in`), 60ms stagger.
- Toast with slide+fade entrance via transition (not keyframes).
- Signal: subtle ambient pulse. Pill `alarm-on`: a breathing dot.
- `prefers-reduced-motion`: globally neutralizes transforms/animations; `@media (hover:hover)` gates the hovers.

## Verification

- All 3 pages return 200 with the new elements (hero/console/signal/steam; brand/wizard/mono).
- Computed: `body` bg `#121010`, `--rust #db4325`, telemetry `ui-monospace`, card radius 14px, "Conectada" pill in signal green, mono quota. No console errors.
- Pending: **visual screenshot review** — the browser pane was not compositing frames this session, so validation was by measurement/DOM, not by eye. Still need to look on screen and tune fine details (emil: "review the next day with fresh eyes").

## Note

The `agents-design-experience@buildwithclaude` plugin was not installed (needs `/plugin` in an interactive terminal); it was not needed, the skills covered the work. The design skill used is `frontend-design` from [anthropics/skills](https://github.com/anthropics/skills).
