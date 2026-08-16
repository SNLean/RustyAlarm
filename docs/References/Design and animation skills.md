---
title: Design and animation skills
tags:
  - reference
  - tooling
  - ui
  - animation
aliases:
  - emil skills
  - emilkowalski skills
  - frontend-design
---

# Design and animation skills

Skills installed to improve UI and motion. Installed globally in `~/.claude/skills/` and copied into the repo at `skills/`. Used to polish the [[Subscription service]] panel and landing.

## Emil Kowalski's skills

- Repo: [github.com/emilkowalski/skills](https://github.com/emilkowalski/skills)
- Install/update: `npx skills@latest add emilkowalski/skills`

**Core (design + animation)**

| Skill | What it does |
|---|---|
| `emil-design-eng` | UI polish, animation decisions, the details that make software feel right |
| `apple-design` | Apple principles: fluid motion, gestures, springs, materials, typography |
| `animate` | Builds an animation from scratch: curve, duration, properties, entry/exit |

**Audit / improve**

| Skill | What it does |
|---|---|
| `find-animation-opportunities` | Finds where motion is missing (and where NOT to add it). Read-only |
| `improve-animations` | Audits all animations and gives a prioritized plan |
| `review-animations` | Strict review of a single animation |
| `animation-vocabulary` | Gives the exact name of an effect |

**Assume React (less applicable today)**: `ask-sonner`, `pick-ui-library`, `prototype`.

## Anthropic's design skill

- `frontend-design` — from [anthropics/skills](https://github.com/anthropics/skills): visual direction, typography, avoiding a templated look. Install: `npx skills@latest add anthropics/skills -s frontend-design`.

> [!note] Fit with the project
> The panel (`saas/templates/`) and landing are vanilla HTML/CSS/JS. `animate`, `apple-design`, `emil-design-eng`, `frontend-design`, `find-animation-opportunities`, `review-animations` and `animation-vocabulary` apply well. The React ones (`ask-sonner`, `pick-ui-library`) only if the front is migrated. See [[Log/2026-08-15 — Frontend redesign]].

## Other UI skills already available (not emil's)

- `baseline-ui` — quick deslop: spacing, hierarchy, typography.
- `fixing-motion-performance` — fixes animation jank (compositor, layout thrashing).
- `design-review` — designer's eye: visual inconsistency and slow interactions.
