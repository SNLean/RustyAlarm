---
title: 2026-08-15 — Skills de diseño y animación
tags:
  - registro
  - sesion
  - herramientas
date: 2026-08-15
---

# 2026-08-15 — Skills de diseño y animación

Se instalaron las skills de [[Skills de diseño y animación|Emil Kowalski]] para mejorar UI y animaciones.

## Qué se hizo

1. **Instalación** de las 10 skills de [emilkowalski/skills](https://github.com/emilkowalski/skills) a nivel global (`~/.claude/skills/`) con `npx skills@latest add emilkowalski/skills -g -s '*' -y --copy`. 8 ya estaban; nuevas: `pick-ui-library` y `prototype`.
2. **Copia al repo** en `skills/` (con `skills/README.md`) para que viajen versionadas con el proyecto.
3. **Doc en el vault**: [[Skills de diseño y animación]] con qué hace cada una y cuáles aplican al panel/landing vanilla.

## Notas

- El instalador tiró "Failed to install 10 → PromptScript": es otro agente distinto de Claude Code, no afecta; los archivos de Claude se copiaron OK.
- `pick-ui-library` y `prototype` traen `disable-model-invocation: true` → solo corren si se las invoca explícitamente.
- Encaje: el front de RustyAlarm es HTML/CSS/JS vanilla, así que aplican sobre todo las de animación/diseño; las de React (`ask-sonner`, `pick-ui-library`) menos.

## Pendiente

- Correr `find-animation-opportunities` sobre `saas/templates/` y la landing para sacar puntos concretos de mejora (pill "SONANDO", transición de cards, modal del editor, feedback de botones).

## Fuentes

- [emilkowalski/skills](https://github.com/emilkowalski/skills)
- [skills CLI (npx skills)](https://www.npmjs.com/package/skills)
