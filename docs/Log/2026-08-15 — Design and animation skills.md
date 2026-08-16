---
title: 2026-08-15 — Design and animation skills
tags:
  - log
  - session
  - tooling
date: 2026-08-15
---

# 2026-08-15 — Design and animation skills

Installed [[Design and animation skills|Emil Kowalski's skills]] to improve UI and animations.

## What was done

1. **Installed** the 10 skills from [emilkowalski/skills](https://github.com/emilkowalski/skills) globally (`~/.claude/skills/`) with `npx skills@latest add emilkowalski/skills -g -s '*' -y --copy`. 8 were already present; new: `pick-ui-library` and `prototype`.
2. **Copied into the repo** at `skills/` (with `skills/README.md`) so they are versioned with the project.
3. **Documented in the vault**: [[Design and animation skills]] with what each does and which apply to the vanilla panel/landing.

## Notes

- The installer printed "Failed to install 10 → PromptScript": that is a different agent from Claude Code, harmless; the Claude files copied fine.
- `pick-ui-library` and `prototype` carry `disable-model-invocation: true` → they only run when invoked explicitly.
- Fit: RustyAlarm's front is vanilla HTML/CSS/JS, so the animation/design ones apply most; the React ones (`ask-sonner`, `pick-ui-library`) less.

## Pending

- Run `find-animation-opportunities` over `saas/templates/` and the landing for concrete improvement points.

## Sources

- [emilkowalski/skills](https://github.com/emilkowalski/skills)
- [skills CLI (npx skills)](https://www.npmjs.com/package/skills)
